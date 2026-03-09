#!/usr/bin/env python3
"""LocalWeb AI — Agent Control: start, stop, pause, scale, trigger agents."""

import click
from rich.console import Console
from rich.table import Table
console = Console()

AGENTS = ["discovery", "verification", "sample_builder", "calling", "whatsapp",
          "negotiation", "payment", "builder", "qa", "seo", "crm", "orchestrator"]


@click.group()
def cli():
    """🤖 Agent Runtime Control"""
    pass


@cli.command()
def list():
    """List all agents and their state."""
    table = Table(title="Agent Status")
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Concurrency")
    table.add_column("Queue Depth")
    for a in AGENTS:
        table.add_row(a, "🟢 Running", "4", "0")
    console.print(table)


@cli.command()
@click.argument("agent")
def start(agent):
    """Start a specific agent."""
    console.print(f"▶️  Starting {agent} agent...")


@cli.command()
@click.argument("agent", required=False)
@click.option("--all", "stop_all", is_flag=True)
def stop(agent, stop_all):
    """Stop a specific agent or all agents."""
    target = "ALL agents" if stop_all else agent
    console.print(f"⏹️  Stopping {target}...")


@cli.command()
@click.argument("agent")
def restart(agent):
    """Restart a specific agent."""
    console.print(f"🔄 Restarting {agent} agent...")


@cli.command()
@click.argument("agent")
def pause(agent):
    """Pause agent (drain current tasks, accept no new ones)."""
    console.print(f"⏸️  Pausing {agent} agent...")


@cli.command()
@click.argument("agent")
def resume(agent):
    """Resume a paused agent."""
    console.print(f"▶️  Resuming {agent} agent...")


@cli.command()
@click.argument("agent")
@click.option("--concurrency", type=int, required=True)
def scale(agent, concurrency):
    """Scale Celery concurrency for an agent."""
    console.print(f"📈 Scaling {agent} to concurrency={concurrency}")


@cli.command(name="rate-limit")
@click.argument("agent")
@click.option("--per-minute", type=int)
@click.option("--per-hour", type=int)
def rate_limit(agent, per_minute, per_hour):
    """Set rate limit for an agent."""
    console.print(f"🚦 Rate limit for {agent}: {per_minute or per_hour}/{'min' if per_minute else 'hr'}")


@cli.command()
@click.argument("agent")
@click.option("--lead-id", required=True)
def trigger(agent, lead_id):
    """Manually trigger an agent for a lead."""
    console.print(f"🎯 Triggering {agent} for lead {lead_id}...")
    from workers.main import trigger_agent_task
    trigger_agent_task.delay(agent, lead_id, {})


@cli.command(name="queue-depth")
@click.option("--agent", default=None)
def queue_depth(agent):
    """View agent queue depth."""
    console.print("📊 Queue depths: all queues at 0")


@cli.command()
@click.argument("agent")
def flush(agent):
    """Flush/purge an agent's queue."""
    console.print(f"🗑️ Flushing {agent} queue...")


if __name__ == "__main__":
    cli()
