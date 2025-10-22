import asyncio
import aiohttp
import yaml
import time
import typer
from rich.console import Console
from rich.table import Table

# cli + console setup
app = typer.Typer(help="Async API Health Monitor CLI")
console = Console()

# async api check
async def check_api(session, api):
    url = api["url"]
    name = api.get("name", url)
    start = time.time()
    try:
        async with session.get(url, timeout=5) as resp:
            latency = (time.time() - start) * 1000
            return name, resp.status, latency
    except Exception:
        latency = (time.time() - start) * 1000
        return name, None, latency

# slack/discord alert
async def send_alert(session, webhook_url, message):
    if not webhook_url:
        return
    payload = {"text": message} if "slack" in webhook_url else {"content": message}
    try:
        async with session.post(webhook_url, json=payload):
            pass
    except Exception as e:
        console.print(f"[red]Failed to send alert:[/red] {e}")

# main checker
async def run_checks(config_path: str):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    apis = config.get("apis", [])
    alerts = config.get("alerts", {})
    slack_webhook = alerts.get("slack")
    discord_webhook = alerts.get("discord")

    if not apis:
        console.print("[red]No APIs found in the config file![/red]")
        return

    table = Table(title="🚦 API Health Monitor (Async)")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Latency (ms)", justify="right")

    async with aiohttp.ClientSession() as session:
        tasks = [check_api(session, api) for api in apis]
        results = await asyncio.gather(*tasks)

        failed_apis = []
        for name, status, latency in results:
            if status == 200:
                status_text = f"[green]{status} OK[/green]"
            elif status is None:
                status_text = "[red]DOWN[/red]"
                failed_apis.append(name)
            else:
                status_text = f"[red]{status} FAIL[/red]"
                failed_apis.append(name)
            table.add_row(name, status_text, f"{latency:.1f}")

        console.print(table)

        # alerts
        if failed_apis:
            message = f"⚠️ API(s) failed: {', '.join(failed_apis)}"
            await asyncio.gather(
                send_alert(session, slack_webhook, message),
                send_alert(session, discord_webhook, message)
            )
            console.print(f"[bold red]Sent alert for failed APIs: {failed_apis}[/bold red]")
        else:
            console.print("[green]All APIs healthy![/green]")

# typer commands
@app.command()
def check(
    config_path: str = typer.Argument(..., help="Path to your YAML config file.")
):
    """Run async API health checks and send alerts"""
    asyncio.run(run_checks(config_path))

@app.command()
def list(config_path: str = typer.Argument(..., help="Path to your YAML config file.")):
    """List all APIs in the config file"""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    apis = config.get("apis", [])
    if not apis:
        console.print("[red]No APIs found in the config file![/red]")
        raise typer.Exit()

    table = Table(title="📜 Configured APIs")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="magenta")

    for api in apis:
        table.add_row(api.get("name", "Unknown"), api.get("url", ""))
    console.print(table)

#entry point
if __name__ == "__main__":
    app()