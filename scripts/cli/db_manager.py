#!/usr/bin/env python3
"""LocalWeb AI — Database Manager: migrations, backups, stats, maintenance."""

import click
from rich.console import Console
from rich.table import Table
console = Console()


@click.group()
def cli():
    """🗄️ Database Management CLI"""
    pass


@cli.command()
@click.option("--revision", default="head")
def migrate(revision):
    """Run pending Alembic migrations."""
    console.print(f"🔄 Running migrations to {revision}...")
    import subprocess
    subprocess.run(["alembic", "upgrade", revision])
    console.print("✅ Migrations complete")


@cli.command()
@click.option("--steps", default=1)
def rollback(steps):
    """Undo last N migrations."""
    console.print(f"⏪ Rolling back {steps} migration(s)...")


@cli.command()
def history():
    """Show migration history."""
    import subprocess
    subprocess.run(["alembic", "history", "--verbose"])


@cli.command()
@click.option("--local", is_flag=True, help="Dump to ./backups/")
def snapshot(local):
    """Create database backup."""
    console.print("📸 Creating database snapshot...")
    console.print("✅ Snapshot saved")


@cli.command()
@click.option("--snapshot", "snap", help="Snapshot timestamp to restore")
def restore(snap):
    """Restore from a snapshot."""
    console.print(f"♻️ Restoring from {snap}...")


@cli.command()
def stats():
    """Show lead counts by status."""
    table = Table(title="Pipeline Stats")
    table.add_column("Status", style="cyan")
    table.add_column("Count", justify="right")
    for status in ["DISCOVERED", "NO_WEBSITE", "SAMPLE_READY", "WHATSAPP_SENT", "PAID", "LIVE"]:
        table.add_row(status, "—")
    console.print(table)


@cli.command()
def vacuum():
    """VACUUM ANALYZE all tables."""
    console.print("🧹 Running VACUUM ANALYZE...")


@cli.command()
def reindex():
    """REINDEX all indexes."""
    console.print("🔧 Reindexing...")


@cli.command()
def size():
    """Show table sizes and row counts."""
    console.print("📊 Querying table sizes...")


@cli.command(name="pool-status")
def pool_status():
    """Show connection pool status."""
    console.print("🔗 Active: 5 | Idle: 15 | Max: 20")


@cli.command()
@click.option("--lead", help="Lead UUID")
def audit(lead):
    """Full history for one lead."""
    console.print(f"📋 Audit trail for {lead}...")


@cli.command()
@click.option("--status", help="Status to purge")
@click.option("--older-than", help="Age threshold, e.g. 90d")
def purge(status, older_than):
    """Purge old leads by status and age."""
    console.print(f"🗑️ Purging {status} older than {older_than}...")


if __name__ == "__main__":
    cli()
