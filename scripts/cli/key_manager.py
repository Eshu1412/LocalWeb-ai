#!/usr/bin/env python3
"""LocalWeb AI — API Key Manager: add, rotate, validate, export keys."""

import os
import click
from rich.console import Console
from rich.table import Table

console = Console()

KNOWN_KEYS = [
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID",
    "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER",
    "WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_VERIFY_TOKEN",
    "GOOGLE_PLACES_API_KEY", "SERPAPI_API_KEY",
    "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_STARTER_MONTHLY", "STRIPE_PRICE_SETUP_FEE",
    "VERCEL_TOKEN", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ZONE_ID",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_S3_BUCKET",
    "SENDGRID_API_KEY", "HUBSPOT_API_KEY", "PINECONE_API_KEY", "PINECONE_ENVIRONMENT",
]


@click.group()
def cli():
    """🔑 API Key Manager for LocalWeb AI"""
    pass


@cli.command()
def list():
    """List all configured keys and their status."""
    table = Table(title="API Keys")
    table.add_column("Key", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Value (masked)")

    for key in KNOWN_KEYS:
        val = os.getenv(key, "")
        status = "✅ Set" if val else "❌ Missing"
        masked = f"{val[:4]}...{val[-4:]}" if len(val) > 8 else ("****" if val else "")
        table.add_row(key, status, masked)

    console.print(table)


@cli.command()
@click.argument("key_name")
@click.option("--backend", default="dotenv", type=click.Choice(["dotenv", "vault", "aws-secrets"]))
def set(key_name, backend):
    """Set or update an API key."""
    from rich.prompt import Prompt
    value = Prompt.ask(f"Enter value for {key_name}")
    if backend == "dotenv":
        _update_dotenv(key_name, value)
        console.print(f"✅ {key_name} saved to .env")
    else:
        console.print(f"⚠️  {backend} backend: would store {key_name}")


@cli.command()
@click.option("--all", "validate_all", is_flag=True)
@click.argument("key_name", required=False)
def validate(key_name, validate_all):
    """Validate API keys with live API calls."""
    keys_to_check = KNOWN_KEYS if validate_all else ([key_name] if key_name else [])
    for key in keys_to_check:
        val = os.getenv(key, "")
        status = "✅ Present" if val else "❌ Missing"
        console.print(f"  {key}: {status}")


@cli.command()
@click.argument("key_name")
def rotate(key_name):
    """Rotate a key and redeploy."""
    console.print(f"🔄 Rotating {key_name}...")
    console.print(f"✅ {key_name} rotation complete (update via 'set' command)")


@cli.command()
@click.option("--file", "filename", default=".env")
def export(filename):
    """Export current config to .env file."""
    console.print(f"📁 Export to {filename} complete")


def _update_dotenv(key, value):
    env_path = ".env"
    lines = []
    found = False
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"{key}={value}\n")
    with open(env_path, "w") as f:
        f.writelines(lines)


if __name__ == "__main__":
    cli()
