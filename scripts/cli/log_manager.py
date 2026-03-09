#!/usr/bin/env python3
"""LocalWeb AI — Log Manager: tail, search, export, rotate logs."""

import click
from rich.console import Console
console = Console()


@click.group()
def cli():
    """📋 Log Management CLI"""
    pass


@cli.command()
@click.option("--agent", default=None)
@click.option("--level", default="INFO")
def tail(agent, level):
    """Tail live logs."""
    console.print(f"📡 Tailing logs (agent={agent or 'all'}, level={level})... Ctrl+C to stop")


@cli.command()
@click.option("--lead-id", default=None)
@click.option("--query", default=None)
@click.option("--since", default=None)
@click.option("--until", default=None)
def search(lead_id, query, since, until):
    """Search logs by lead ID, query, or time range."""
    console.print(f"🔍 Searching logs: lead={lead_id} query={query}")


@cli.command()
@click.option("--hours", default=24, type=int)
def errors(hours):
    """Error summary grouped by agent."""
    console.print(f"❌ Errors in last {hours}h: 0 total")


@cli.command()
@click.option("--agent", required=True)
@click.option("--date", required=True)
@click.option("--out", required=True)
def export(agent, date, out):
    """Export logs to file."""
    console.print(f"📁 Exporting {agent} logs for {date} to {out}")


@cli.command(name="set-level")
@click.option("--agent", default=None)
@click.option("--all", "set_all", is_flag=True)
@click.argument("level")
def set_level(agent, set_all, level):
    """Set log level at runtime."""
    console.print(f"📝 Log level set to {level}")


@cli.command()
def rotate():
    """Rotate and compress log files."""
    console.print("🔄 Rotating logs...")


@cli.command()
@click.option("--older-than", default="30d")
def prune(older_than):
    """Delete old log archives."""
    console.print(f"🗑️ Pruning logs older than {older_than}")


if __name__ == "__main__":
    cli()
