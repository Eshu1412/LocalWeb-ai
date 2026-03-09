"""Calling Agent — Voice call script prompt."""

CALLING_SCRIPT_PROMPT = """Business name: {name}
Owner name (if known): {owner_name}
Category: {category}
Preview URL: {preview_url}
Area: {area}

Write a friendly, natural-sounding 60-second phone script.
The agent tells the owner about a free website we built for them.
Use natural pauses (written as '...'). Start with a greeting that sounds local.
Never sound robotic or salesy. End by asking if they can check WhatsApp for the link.
Cover: greeting, who we are, what we built, the preview link, price ($49/mo), WhatsApp CTA."""
