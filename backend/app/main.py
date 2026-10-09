import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db import get_session, engine
from app.models import Base, Material, PriceSnapshot
from app.config import settings
from app.collector import run_collector, seed_materials
from app.stats import calculate_time_window_stats, calculate_moving_average, calculate_volatility
from app.signals import evaluate_sell_signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wow_market")

scheduler = AsyncIOScheduler()

async def run_collector_job():
    """وظیفه دوره‌ای زمان‌بند برای استخراج و همگام‌سازی قیمت‌ها"""
    try:
        logger.info("[Scheduler] Starting scheduled collector run...")
        async for session in get_session():
            await run_collector(db=session, region=settings.WOW_REGION)
            break
    except Exception as e:
        logger.error(f"[Scheduler] Error running collector job: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ۱. اطمینان از ایجاد جداول دیتابیس
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ۲. Seed اولیه آیتم‌ها
    async for session in get_session():
        await seed_materials(session)
        break

    # ۳. راه‌اندازی زمان‌بند (APScheduler)
    scheduler.add_job(
        run_collector_job,
        'interval',
        hours=settings.COLLECTOR_INTERVAL_HOURS,
        id='hourly_collector',
        replace_existing=True
    )
    scheduler.start()
    logger.info("[Lifespan] Scheduler started.")
    
    yield
    
    scheduler.shutdown()
    logger.info("[Lifespan] Scheduler stopped.")

app = FastAPI(
    title="WoW Midnight Market Tracker API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "region": settings.WOW_REGION}

@app.get("/api/materials")
async def get_materials(
    profession: str = Query(None),
    region: str = Query("eu"),
    session: AsyncSession = Depends(get_session)
):
    query = select(Material).where(Material.active == True)
    if profession and profession.lower() != "all":
        query = query.where(Material.profession == profession.lower())
    
    res = await session.execute(query)
    materials = res.scalars().all()

    results = []
    for mat in materials:
        snap_query = select(PriceSnapshot).where(
            PriceSnapshot.item_id == mat.item_id,
            PriceSnapshot.region == region.lower()
        ).order_by(PriceSnapshot.snapshot_at.desc()).limit(1)
        
        snap_res = await session.execute(snap_query)
        latest = snap_res.scalars().first()

        results.append({
            "id": mat.id,
            "item_id": mat.item_id,
            "name": mat.name,
            "profession": mat.profession,
            "current_price_copper": latest.price_copper if latest else None,
            "current_price_gold": round(latest.price_copper / 10000.0, 2) if latest else None,
            "quantity": latest.quantity if latest else None,
            "last_updated": latest.snapshot_at.isoformat() if latest and latest.snapshot_at else None
        })
    return results

@app.get("/api/materials/{item_id}/history")
async def get_material_history(
    item_id: int,
    region: str = Query("eu"),
    period: str = Query("30d"),
    session: AsyncSession = Depends(get_session)
):
    query = select(PriceSnapshot).where(
        PriceSnapshot.item_id == item_id,
        PriceSnapshot.region == region.lower()
    ).order_by(PriceSnapshot.snapshot_at.asc())

    res = await session.execute(query)
    snapshots = res.scalars().all()

    if not snapshots:
        raise HTTPException(status_code=404, detail="No historical data found for this item.")

    return [
        {
            "timestamp": s.snapshot_at.isoformat(),
            "price_gold": round(s.price_copper / 10000.0, 2),
            "quantity": s.quantity
        }
        for s in snapshots
    ]

@app.get("/api/materials/{item_id}/stats")
async def get_material_stats(
    item_id: int,
    region: str = Query("eu"),
    period: str = Query("30d"),
    session: AsyncSession = Depends(get_session)
):
    query = select(PriceSnapshot).where(
        PriceSnapshot.item_id == item_id,
        PriceSnapshot.region == region.lower()
    ).order_by(PriceSnapshot.snapshot_at.asc())
    
    res = await session.execute(query)
    snapshots = res.scalars().all()

    if not snapshots:
        raise HTTPException(status_code=404, detail="No price data available for item")

    prices = [s.price_copper for s in snapshots]
    quantities = [s.quantity for s in snapshots]
    current = prices[-1]

    stats_30d = calculate_time_window_stats(prices, current)
    ma_30 = calculate_moving_average(prices, min(30, len(prices))) or float(current)
    volatility = calculate_volatility(prices)

    signal = evaluate_sell_signal(
        current_price=current,
        percentile_30d=stats_30d["percentile"],
        percentile_7d=stats_30d["percentile"],
        momentum_24h=stats_30d["change_percent"],
        momentum_6h=stats_30d["change_percent"] / 2.0,
        ma_30d=ma_30,
        supply_percentile=50.0,
        high_30d=stats_30d["high"]
    )

    return {
        "item_id": item_id,
        "current_copper": current,
        "current_gold": round(current / 10000.0, 2),
        "high_gold": round(stats_30d["high"] / 10000.0, 2),
        "low_gold": round(stats_30d["low"] / 10000.0, 2),
        "avg_gold": round(stats_30d["average"] / 10000.0, 2),
        "change_percent": stats_30d["change_percent"],
        "volatility": volatility,
        "signal": signal
    }

@app.post("/api/collector/run")
async def trigger_collector(
    region: str = Query("eu"),
    session: AsyncSession = Depends(get_session)
):
    result = await run_collector(db=session, region=region)
    return result
