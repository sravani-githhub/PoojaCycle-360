from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, server_default=func.now(), nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('admin','organizer','collector','artisan','processing_partner','customer')", name="ck_users_role"), CheckConstraint("account_status IN ('active','inactive','suspended')", name="ck_users_status"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(32))
    location: Mapped[str | None] = mapped_column(String(200))
    account_status: Mapped[str] = mapped_column(String(20), default="active", server_default="active", nullable=False)


class WasteSource(TimestampMixin, Base):
    __tablename__ = "waste_sources"
    __table_args__ = (CheckConstraint("source_type IN ('temple','festival','community_site')", name="ck_sources_type"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(180), nullable=False)
    source_type: Mapped[str] = mapped_column(String(24), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(160))
    contact_phone: Mapped[str | None] = mapped_column(String(32))


class WasteType(Base):
    __tablename__ = "waste_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    handling_notes: Mapped[str] = mapped_column(Text, nullable=False)
    reports: Mapped[list["WasteReport"]] = relationship(back_populates="waste_type")


class WasteReport(TimestampMixin, Base):
    __tablename__ = "waste_reports"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_waste_reports_quantity_positive"), CheckConstraint("unit IN ('kg','g','tonne','item')", name="ck_waste_reports_unit"), CheckConstraint("collection_status IN ('pending','assigned','scheduled','collected','cancelled','failed')", name="ck_waste_reports_status"), CheckConstraint("contamination_level IS NULL OR (contamination_level >= 0 AND contamination_level <= 100)", name="ck_waste_reports_contamination"), CheckConstraint("preferred_pickup_window IS NULL OR preferred_pickup_window IN ('morning','midday','evening')", name="ck_waste_reports_pickup_window"), Index("ix_waste_reports_status_availability", "collection_status", "availability_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("waste_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    waste_type_id: Mapped[int] = mapped_column(ForeignKey("waste_types.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), default="kg", nullable=False)
    contamination_level: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    contamination_notes: Mapped[str | None] = mapped_column(Text)
    availability_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    preferred_pickup_window: Mapped[str | None] = mapped_column(String(12))
    festival_collection: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    collection_status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    reported_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    source: Mapped[WasteSource] = relationship()
    waste_type: Mapped[WasteType] = relationship(back_populates="reports")


class CollectionAssignment(TimestampMixin, Base):
    __tablename__ = "collection_assignments"
    __table_args__ = (CheckConstraint("status IN ('pending','assigned','scheduled','collected','cancelled','failed')", name="ck_assignments_status"), Index("ix_assignments_status_pickup", "status", "scheduled_pickup_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    waste_report_id: Mapped[int] = mapped_column(ForeignKey("waste_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    collector_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    scheduled_pickup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_pickup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class WasteBatch(TimestampMixin, Base):
    __tablename__ = "waste_batches"
    __table_args__ = (CheckConstraint("received_quantity > 0", name="ck_batches_quantity_positive"), CheckConstraint("unit IN ('kg','g','tonne','item')", name="ck_batches_unit"), CheckConstraint("current_stage IN ('received','sorted','in_processing','processed','composted','reused','recycled','rejected')", name="ck_batches_stage"), UniqueConstraint("waste_report_id", name="uq_batch_report"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    waste_report_id: Mapped[int] = mapped_column(ForeignKey("waste_reports.id", ondelete="RESTRICT"), nullable=False)
    waste_type_id: Mapped[int] = mapped_column(ForeignKey("waste_types.id", ondelete="RESTRICT"), nullable=False)
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), default="kg", nullable=False)
    current_stage: Mapped[str] = mapped_column(String(20), default="received", nullable=False)
    quality_notes: Mapped[str | None] = mapped_column(Text)


class ProcessingRecord(TimestampMixin, Base):
    __tablename__ = "processing_records"
    __table_args__ = (CheckConstraint("input_quantity > 0", name="ck_processing_input_positive"), CheckConstraint("input_unit IN ('kg','g','tonne','item')", name="ck_processing_input_unit"), CheckConstraint("output_quantity IS NULL OR output_quantity >= 0", name="ck_processing_output_nonnegative"), CheckConstraint("output_unit IS NULL OR output_unit IN ('kg','g','tonne','item')", name="ck_processing_output_unit"), CheckConstraint("(output_quantity IS NULL AND output_unit IS NULL) OR (output_quantity IS NOT NULL AND output_unit IS NOT NULL)", name="ck_processing_output_unit_required"), CheckConstraint("status IN ('planned','in_progress','completed','failed')", name="ck_processing_status"), CheckConstraint("processing_method IN ('composting','coir_production','craft_production','paper_making','reuse_upcycling','authorized_recycling','sorting','other')", name="ck_processing_method"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("waste_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    processing_partner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    processing_method: Mapped[str] = mapped_column(String(40), nullable=False)
    input_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    input_unit: Mapped[str] = mapped_column(String(10), default="kg", nullable=False)
    output_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    output_unit: Mapped[str | None] = mapped_column(String(10))
    output_description: Mapped[str | None] = mapped_column(Text)
    processing_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="planned", nullable=False)
    evidence_notes: Mapped[str | None] = mapped_column(Text)


class Artisan(TimestampMixin, Base):
    __tablename__ = "artisans"
    __table_args__ = (CheckConstraint("availability_status IN ('available','busy','inactive')", name="ck_artisans_availability"), CheckConstraint("contact_visibility IN ('private','platform_only','public')", name="ck_artisans_visibility"),)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), unique=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    skills: Mapped[str] = mapped_column(Text, nullable=False)
    preferred_materials: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(254))
    monthly_capacity_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    availability_status: Mapped[str] = mapped_column(String(20), default="available", nullable=False)
    contact_visibility: Mapped[str] = mapped_column(String(20), default="private", nullable=False)


class ArtisanMaterialRequest(TimestampMixin, Base):
    __tablename__ = "artisan_material_requests"
    __table_args__ = (CheckConstraint("required_quantity > 0", name="ck_material_request_quantity_positive"), CheckConstraint("unit IN ('kg','g','tonne','item')", name="ck_material_request_unit"), CheckConstraint("status IN ('open','matched','fulfilled','cancelled')", name="ck_material_request_status"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    artisan_id: Mapped[int] = mapped_column(ForeignKey("artisans.id", ondelete="CASCADE"), nullable=False, index=True)
    waste_type_id: Mapped[int] = mapped_column(ForeignKey("waste_types.id", ondelete="RESTRICT"), nullable=False)
    required_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), default="kg", nullable=False)
    request_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (CheckConstraint("price >= 0", name="ck_products_price_nonnegative"), CheckConstraint("available_stock >= 0", name="ck_products_stock_nonnegative"), CheckConstraint("status IN ('draft','active','out_of_stock','archived')", name="ck_products_status"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    artisan_id: Mapped[int | None] = mapped_column(ForeignKey("artisans.id", ondelete="SET NULL"), index=True)
    product_name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    available_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)


class ProductBatch(Base):
    __tablename__ = "product_batches"
    __table_args__ = (UniqueConstraint("product_id", "batch_id", name="uq_product_batch"), CheckConstraint("quantity_used > 0", name="ck_product_batches_quantity_positive"), CheckConstraint("unit IN ('kg','g','tonne','item')", name="ck_product_batches_unit"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("waste_batches.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity_used: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), default="kg", nullable=False)


class CustomerOrder(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (CheckConstraint("total_amount >= 0", name="ck_orders_total_nonnegative"), CheckConstraint("status IN ('pending','confirmed','shipped','completed','cancelled')", name="ck_orders_status"), CheckConstraint("payment_mode = 'simulated'", name="ck_orders_simulated_payment"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    payment_mode: Mapped[str] = mapped_column(String(20), default="simulated", nullable=False)
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"), CheckConstraint("unit_price >= 0 AND subtotal >= 0", name="ck_order_items_amounts_nonnegative"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    order: Mapped[CustomerOrder] = relationship(back_populates="items")


class ImpactRecord(Base):
    __tablename__ = "impact_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("waste_batches.id", ondelete="CASCADE"), index=True)
    processing_record_id: Mapped[int | None] = mapped_column(ForeignKey("processing_records.id", ondelete="CASCADE"), index=True)
    measured_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity_basis: Mapped[str] = mapped_column(String(16), nullable=False)
    outcome_category: Mapped[str] = mapped_column(String(50), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(24), default="unverified", nullable=False)
    evidence_reference: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
