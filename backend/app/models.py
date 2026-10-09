from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, DateTime, Float, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    profession = Column(String(50), nullable=False, default="herbalism", index=True)  # herbalism, mining
    expansion = Column(String(50), nullable=False, default="midnight")
    active = Column(Boolean, default=True)

    snapshots = relationship("PriceSnapshot", back_populates="material", cascade="all, delete-orphan")

    # Property alias for backward/forward compatibility
    @hybrid_property
    def category(self):
        return self.profession

    @category.setter
    def category(self, value):
        self.profession = value


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)  # eu, us, kr, tw
    name = Column(String(50), nullable=False)


class Realm(Base):
    __tablename__ = "realms"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    connected_realm_id = Column(Integer, nullable=True)


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    region = Column(String(10), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("materials.item_id"), nullable=False, index=True)
    snapshot_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    price_copper = Column(BigInteger, nullable=False)
    quantity = Column(BigInteger, nullable=False)
    source_updated_at = Column(DateTime, nullable=True)

    material = relationship("Material", back_populates="snapshots")

    __table_args__ = (
        UniqueConstraint("region", "item_id", "source_updated_at", name="uq_snapshot_source_time"),
        Index("idx_item_region_time", "item_id", "region", "snapshot_at"),
    )


class PriceDaily(Base):
    __tablename__ = "price_daily"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    region = Column(String(10), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("materials.item_id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(BigInteger, nullable=False)
    high = Column(BigInteger, nullable=False)
    low = Column(BigInteger, nullable=False)
    close = Column(BigInteger, nullable=False)
    average = Column(BigInteger, nullable=False)
    volume = Column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("region", "item_id", "date", name="uq_daily_item_region_date"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="default_user")
    item_id = Column(Integer, ForeignKey("materials.item_id"), nullable=False)
    region = Column(String(10), nullable=False)
    alert_type = Column(String(50), nullable=False)  # PRICE_ABOVE, PERCENTILE_ABOVE, SELL_SCORE_ABOVE
    threshold = Column(Float, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
