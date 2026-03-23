"""Click CLI for the deal aggregator."""

from __future__ import annotations

import asyncio
import logging

import click
from rich.console import Console
from rich.table import Table

from aggregator.db import init_db, query_deals, upsert_deals, upsert_reviews
from aggregator.auth_db import init_auth_db, create_invite_codes, list_invite_codes
from aggregator.scraper import scrape_all

console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
def cli(verbose: bool) -> None:
    """snow-deals aggregator — scrape and rank ski/snowboard deals."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )


@cli.command()
@click.option("--delay", "-d", type=float, default=1.0, help="Delay between requests.")
@click.option("--max-pages", type=int, default=25, help="Max pages per store.")
def refresh(delay: float, max_pages: int) -> None:
    """Scrape all stores and update the database."""
    async def _run() -> None:
        await init_db()
        with console.status("[bold cyan]Scraping all stores...", spinner="dots"):
            deals = await scrape_all(delay=delay, max_pages=max_pages)
        console.print(f"[dim]Scraped {len(deals)} deals total.[/dim]")

        if deals:
            count = await upsert_deals(deals)
            console.print(f"[green]Saved {count} deals to database.[/green]")

    asyncio.run(_run())


def _reviews_to_rows(reviews: list) -> list[dict]:
    """Convert ReviewData list to dicts for DB upsert."""
    from datetime import datetime
    return [
        {
            "product_name": r.product_name,
            "brand": r.brand,
            "score": r.score,
            "award": r.award,
            "review_url": r.url,
            "category": r.category,
            "scraped_at": datetime.now().isoformat(),
        }
        for r in reviews
    ]


@cli.command()
@click.option("--delay", "-d", type=float, default=2.0, help="Delay between requests.")
@click.option("--source", type=click.Choice(["ogl", "tgr", "all"]), default="all",
              help="Review source: ogl (OutdoorGearLab), tgr (The Good Ride), or all.")
@click.option("--max-reviews", type=int, default=None,
              help="Max reviews to scrape (TGR only, for testing).")
def fetch_reviews(delay: float, source: str, max_reviews: int | None) -> None:
    """Scrape product review scores from review sites."""
    from aggregator.reviews import scrape_reviews, scrape_tgr_reviews

    async def _run() -> None:
        await init_db()
        total = 0

        if source in ("ogl", "all"):
            with console.status("[bold cyan]Scraping OutdoorGearLab reviews...", spinner="dots"):
                reviews = await scrape_reviews(delay=delay)
            console.print(f"[dim]OGL: scraped {len(reviews)} reviews.[/dim]")
            if reviews:
                count = await upsert_reviews(_reviews_to_rows(reviews))
                total += count
                console.print(f"[green]OGL: saved {count} reviews.[/green]")

        if source in ("tgr", "all"):
            with console.status("[bold cyan]Scraping The Good Ride reviews...", spinner="dots"):
                reviews = await scrape_tgr_reviews(delay=delay, max_reviews=max_reviews)
            console.print(f"[dim]TGR: scraped {len(reviews)} reviews.[/dim]")
            if reviews:
                count = await upsert_reviews(_reviews_to_rows(reviews))
                total += count
                console.print(f"[green]TGR: saved {count} reviews.[/green]")

        console.print(f"[bold green]Total: {total} reviews saved to database.[/bold green]")

    asyncio.run(_run())


@cli.command("generate-codes")
@click.argument("count", type=int, default=10)
def generate_codes(count: int) -> None:
    """Generate invite codes. Usage: snow-deals-agg generate-codes 10"""
    import secrets

    codes = [secrets.token_hex(4).upper() for _ in range(count)]

    async def _run() -> None:
        await init_auth_db()
        created = await create_invite_codes(codes)
        console.print(f"[green]Created {created} invite codes:[/green]")
        for code in codes:
            console.print(f"  [bold cyan]{code}[/bold cyan]")

    asyncio.run(_run())


@cli.command("list-codes")
def list_codes_cmd() -> None:
    """List all invite codes and their usage."""
    async def _run() -> None:
        await init_auth_db()
        codes = await list_invite_codes()
        if not codes:
            console.print("[yellow]No invite codes found.[/yellow]")
            return
        table = Table(title="Invite Codes", show_lines=True)
        table.add_column("Code", style="bold cyan")
        table.add_column("Uses", justify="center")
        table.add_column("Created", style="dim")
        for c in codes:
            uses = str(c["use_count"])
            table.add_row(c["code"], uses, c["created_at"][:16])
        console.print(table)

    asyncio.run(_run())


@cli.command()
@click.option("--category", "-c", default=None, help="Filter by category.")
@click.option("--store", "-s", default=None, help="Filter by store name.")
@click.option("--min-discount", "-m", type=float, default=0, help="Minimum discount %%.")
@click.option("--limit", "-l", type=int, default=50, help="Max results.")
def deals(category: str | None, store: str | None, min_discount: float, limit: int) -> None:
    """Query deals from the database."""
    async def _run() -> None:
        await init_db()
        results = await query_deals(
            category=category, store=store, min_discount=min_discount, limit=limit
        )

        if not results:
            console.print("[yellow]No deals found matching criteria.[/yellow]")
            return

        table = Table(title=f"Top Deals — {len(results)} results", show_lines=True)
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Discount", style="bold green", justify="right", width=10)
        table.add_column("Product", style="white", max_width=50)
        table.add_column("Store", style="cyan", width=20)
        table.add_column("Price", justify="right", width=10)
        table.add_column("Category", style="dim", width=12)

        for i, d in enumerate(results, 1):
            table.add_row(
                str(i),
                f"{d.discount_pct:.0f}%",
                d.name,
                d.store,
                f"${d.current_price:,.2f}",
                d.category or "—",
            )

        console.print(table)

    asyncio.run(_run())
