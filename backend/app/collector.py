import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import AsyncSessionLocal
from app.models import Material, PriceSnapshot


logger = logging.getLogger("wow_market")

UNDERMINE_API_BASE = "https://api.undermine.exchange/v1"

# API key must be prefixed with "ApiKey " — this is the documented format.
API_KEY = "ApiKey AQkyMjkyOTc4MTlp2WYboQEAAEPtgJ_aFcS85X0Jf7Ech6y-9ilx4GBZgMwgWb0"

HEADERS = {
    "Authorization": API_KEY,
    "Accept": "application/json",
    "Accept-Encoding": "gzip",          # required to avoid extra quota usage
}

DEFAULT_REGION = "eu"

TRACKED_ITEMS = [
    {"item_id": 236761, "name": "Sanguithorn", "category": "Herbalism"},
    {"item_id": 236774, "name": "Azeroot", "category": "Herbalism"},
    {"item_id": 237366, "name": "Dazzling Thorium", "category": "Mining"},
    {"item_id": 210796, "name": "Mycobloom (TWW Benchmark)", "category": "Herbalism"},
    {"item_id": 210930, "name": "Bismuth (TWW Benchmark)", "category": "Mining"},
]


def parse_snapshot(value: str) -> datetime:
    """
    Convert an ISO-8601 timestamp to a timezone-naive UTC datetime,
    compatible with TIMESTAMP WITHOUT TIME ZONE in PostgreSQL.
    """
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    utc_dt = parsed.astimezone(timezone.utc)
    return utc_dt.replace(tzinfo=None)


async def seed_materials(db: AsyncSession | None = None) -> int:
    created_count = 0

    async def seed_with_session(session: AsyncSession) -> int:
        nonlocal created_count
        for item in TRACKED_ITEMS:
            result = await session.execute(
                select(Material).where(Material.item_id == item["item_id"])
            )
            material = result.scalar_one_or_none()
            if material is not None:
                continue

            material = Material(
                item_id=item["item_id"],
                name=item["name"],
                category=item["category"],
            )
            session.add(material)
            created_count += 1

        await session.commit()
        return created_count

    if db is not None:
        return await seed_with_session(db)

    async with AsyncSessionLocal() as session:
        return await seed_with_session(session)


async def run_collector(
    db: AsyncSession | None = None,
    region: str | None = None,
) -> int:
    selected_region = (region or DEFAULT_REGION).strip().lower()

    if db is not None:
        return await collect_with_session(db, selected_region)

    async with AsyncSessionLocal() as session:
        return await collect_with_session(session, selected_region)


async def collect_with_session(session: AsyncSession, region: str) -> int:
    print(f"[Collector] Syncing data for region: {region}...")

    await seed_materials(session)

    result = await session.execute(select(Material.item_id))
    item_ids = [row[0] for row in result.all()]

    total_added = 0

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers=HEADERS,             # set headers at client level
    ) as client:
        for item_id in item_ids:
            url = f"{UNDERMINE_API_BASE}/region/{region}/commodities/{item_id}/hourly.json"

            try:
                response = await client.get(url)

                if response.status_code != 200:
                    print(
                        f"[Collector Error] Item {item_id} ({region}) "
                        f"HTTP {response.status_code}: {response.text[:300]}"
                    )
                    continue

                payload = response.json()

                # The payload's hourly series lives under result.hourly.
                hourly_points = payload.get("result", {}).get("hourly", []) or []

                for point in hourly_points:
                    snapshot_raw = point.get("snapshot")
                    if not snapshot_raw:
                        continue

                    snapshot_at = parse_snapshot(snapshot_raw)
                    price_copper = int(point.get("price", 0) or 0)
                    quantity = int(point.get("quantity", 0) or 0)

                    existing = await session.execute(
                        select(PriceSnapshot.id).where(
                            PriceSnapshot.item_id == item_id,
                            PriceSnapshot.region == region,
                            PriceSnapshot.snapshot_at == snapshot_at,
                        )
                    )
                    if existing.scalar_one_or_none() is not None:
                        continue

                    session.add(
                        PriceSnapshot(
                            item_id=item_id,
                            region=region,
                            snapshot_at=snapshot_at,
                            price_copper=price_copper,
                            quantity=quantity,
                        )
                    )
                    total_added += 1

                await session.commit()

            except httpx.HTTPError as exc:
                await session.rollback()
                print(f"[Collector HTTP Error] Item {item_id}: {exc!r}")

            except Exception as exc:
                await session.rollback()
                print(
                    f"[Collector Exception] Item {item_id}: "
                    f"{type(exc).__name__}: {exc}"
                )

    print(f"[Collector] Finished sync. Total points added: {total_added}")
    return total_added
