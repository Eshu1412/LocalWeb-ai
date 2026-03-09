"""
LocalWeb AI — Calling Agent
Places AI voice calls via Twilio + ElevenLabs TTS.
Transcribes responses with Whisper and routes based on intent.
"""

import json

import httpx
from openai import AsyncOpenAI

from agents.base_agent import BaseAgent
from config import settings
from db.models import CallLog
from prompts.calling import CALLING_SCRIPT_PROMPT


class CallingAgent(BaseAgent):
    """
    Outbound AI voice call agent.

    Pipeline: stream:outreach → CallingAgent → stream:negotiate / stream:payment
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def process(self, lead_id: str, payload: dict) -> dict:
        """Route to appropriate calling action."""
        action = payload.get("action", "initiate_call")
        if action == "initiate_call":
            return await self.initiate_call(lead_id, payload)
        elif action == "handle_response":
            return await self.handle_call_response(
                payload["call_sid"], payload["recording_url"]
            )
        return {"error": "Unknown action"}

    async def initiate_call(self, lead_id: str, payload: dict) -> dict:
        """
        Place an AI voice call to the business owner.

        Steps:
            1. Check DNC list and calling window
            2. Generate personalized script with GPT-4o
            3. Convert to audio with ElevenLabs
            4. Place call via Twilio with TwiML
        """
        phone = payload.get("phone")
        if not phone:
            self.logger.error(f"No phone number for lead {lead_id}")
            return {"error": "No phone number"}

        if not settings.CALLING_ENABLED:
            self.logger.info("Calling is disabled — skipping")
            return {"skipped": True, "reason": "calling_disabled"}

        # Check DNC list
        if await self.is_on_dnc(phone):
            self.logger.info(f"Phone {phone} is on DNC list — skipping call")
            await self.update_lead_status(lead_id, "NOT_INTERESTED", "On DNC list")
            return {"skipped": True, "reason": "dnc"}

        # Check calling window (8 AM - 9 PM local time)
        from datetime import datetime
        current_hour = datetime.now().hour
        if not (settings.CALL_WINDOW_START_HOUR <= current_hour < settings.CALL_WINDOW_END_HOUR):
            self.logger.info(f"Outside calling window ({current_hour}h) — scheduling for later")
            return {"skipped": True, "reason": "outside_window", "current_hour": current_hour}

        # 1. Generate personalized script
        script = await self._generate_script(payload)

        # 2. Convert to audio with ElevenLabs
        audio_url = await self._text_to_speech(script)

        # 3. Place call via Twilio
        call_sid = await self._place_call(phone, audio_url)

        # 4. Log the call
        await self._log_call(lead_id, call_sid, phone, script)
        await self.update_lead_status(lead_id, "CALL_INITIATED")

        return {"call_sid": call_sid, "script_length": len(script)}

    async def _generate_script(self, payload: dict) -> str:
        """Generate a personalized 60-second phone pitch."""
        prompt = CALLING_SCRIPT_PROMPT.format(
            name=payload.get("name", ""),
            owner_name=payload.get("owner_name", ""),
            category=payload.get("category", ""),
            preview_url=payload.get("preview_url", ""),
            area=payload.get("area", ""),
        )

        try:
            response = await self.openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Write a natural, friendly 60-second call script. Never sound robotic."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Script generation failed: {e}")
            return (
                f"Hi there! I'm calling from LocalWeb AI. We noticed "
                f"{payload.get('name', 'your business')} doesn't have a website yet, "
                f"so we built a free preview for you. Check your WhatsApp for the link!"
            )

    async def _text_to_speech(self, script: str) -> str:
        """Convert script to audio using ElevenLabs API."""
        if not settings.ELEVENLABS_API_KEY:
            self.logger.warning("ElevenLabs not configured — skipping TTS")
            return ""

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}",
                    headers={
                        "xi-api-key": settings.ELEVENLABS_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": script,
                        "model_id": "eleven_monolingual_v1",
                        "voice_settings": {"stability": 0.75, "similarity_boost": 0.8},
                    },
                )
                if response.status_code == 200:
                    # Upload audio to S3 and return URL
                    audio_url = await self._upload_audio(response.content)
                    return audio_url
        except Exception as e:
            self.logger.error(f"ElevenLabs TTS failed: {e}")
        return ""

    async def _upload_audio(self, audio_data: bytes) -> str:
        """Upload audio file to S3 and return public URL."""
        import uuid
        filename = f"calls/{uuid.uuid4()}.mp3"

        if not settings.AWS_ACCESS_KEY_ID:
            return f"https://{settings.AWS_S3_BUCKET}.s3.amazonaws.com/{filename}"

        try:
            import boto3
            s3 = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )
            s3.put_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=filename,
                Body=audio_data,
                ContentType="audio/mpeg",
                ACL="public-read",
            )
            return f"https://{settings.AWS_S3_BUCKET}.s3.amazonaws.com/{filename}"
        except Exception as e:
            self.logger.error(f"S3 upload failed: {e}")
            return ""

    async def _place_call(self, phone: str, audio_url: str) -> str:
        """Place outbound call via Twilio."""
        if not settings.TWILIO_ACCOUNT_SID:
            self.logger.warning("Twilio not configured — simulating call")
            return f"SIM_{phone}"

        try:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

            twiml = f"""
            <Response>
                <Say>This is an automated call from LocalWeb AI.</Say>
                <Play>{audio_url}</Play>
                <Record maxLength="120"
                        action="{settings.API_BASE_URL}/webhooks/twilio/recording"
                        playBeep="true"/>
            </Response>
            """

            call = client.calls.create(
                to=phone,
                from_=settings.TWILIO_PHONE_NUMBER,
                twiml=twiml,
                status_callback=f"{settings.API_BASE_URL}/webhooks/twilio/call-status",
            )
            self.logger.info(f"Call placed: {call.sid}")
            return call.sid
        except Exception as e:
            self.logger.error(f"Twilio call failed: {e}")
            raise

    async def handle_call_response(self, call_sid: str, recording_url: str) -> dict:
        """Transcribe the owner's response and classify intent."""
        # 1. Transcribe with Whisper
        transcript = await self._transcribe(recording_url)

        # 2. Classify intent
        intent = await self._classify_intent(transcript)

        # 3. Route based on intent
        async with self.db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(CallLog).where(CallLog.call_sid == call_sid)
            )
            call_log = result.scalar_one_or_none()
            if call_log:
                call_log.transcript = transcript
                call_log.intent = intent
                lead_id = str(call_log.lead_id)
                await session.commit()

                if intent == "interested":
                    await self.emit_event("stream:payment", lead_id, {"source": "call"})
                elif intent == "needs_info":
                    await self.emit_event("stream:negotiate", lead_id, {
                        "message": transcript, "channel": "call"
                    })
                else:
                    await self.update_lead_status(lead_id, "NOT_INTERESTED", transcript)

        return {"call_sid": call_sid, "transcript": transcript, "intent": intent}

    async def _transcribe(self, recording_url: str) -> str:
        """Transcribe audio with OpenAI Whisper."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                audio_response = await client.get(recording_url)
                transcript = await self.openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=("recording.wav", audio_response.content, "audio/wav"),
                )
                return transcript.text
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            return ""

    async def _classify_intent(self, transcript: str) -> str:
        """Classify the owner's response intent."""
        if not transcript:
            return "no_response"

        try:
            response = await self.openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Classify the business owner's response. Reply with ONLY one word: interested, needs_info, or not_interested"},
                    {"role": "user", "content": transcript},
                ],
                temperature=0,
                max_tokens=10,
            )
            intent = response.choices[0].message.content.strip().lower()
            return intent if intent in ("interested", "needs_info", "not_interested") else "needs_info"
        except Exception:
            return "needs_info"

    async def _log_call(self, lead_id: str, call_sid: str, phone: str, script: str):
        """Save call record to database."""
        async with self.db() as session:
            log = CallLog(
                lead_id=lead_id,
                call_sid=call_sid,
                from_number=settings.TWILIO_PHONE_NUMBER,
                to_number=phone,
                status="initiated",
                script_used=script,
            )
            session.add(log)
            await session.commit()
