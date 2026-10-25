from datetime import datetime
from decimal import Decimal
from typing import Literal
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


Role = Literal["admin", "organizer", "collector", "artisan", "processing_partner", "customer"]
Unit = Literal["kg", "g", "tonne", "item"]


class UserIn(Input):
    full_name: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=3, max_length=254)
    role: Role
    phone_number: str | None = None
    location: str | None = None
    account_status: Literal["active", "inactive", "suspended"] = "active"

    @field_validator("email")
    @classmethod
    def valid_email_shape(cls, value):
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("enter a valid email address")
        return value.lower()


class SourceIn(Input):
    source_name: str = Field(min_length=1, max_length=180)
    source_type: Literal["temple", "festival", "community_site"]
    address: str = Field(min_length=1)
    contact_name: str | None = None
    contact_phone: str | None = None


class WasteTypeIn(Input):
    name: str = Field(min_length=1, max_length=80)
    description: str
    handling_notes: str


class WasteReportIn(Input):
    source_id: int = Field(gt=0)
    waste_type_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit: Unit = "kg"
    contamination_level: Decimal | None = Field(default=None, ge=0, le=100)
    contamination_notes: str | None = None
    availability_at: datetime
    preferred_pickup_window: Literal["morning", "midday", "evening"] | None = None
    festival_collection: bool = False
    collection_status: Literal["pending", "assigned", "scheduled", "collected", "cancelled", "failed"] = "pending"
    reported_by_user_id: int = Field(gt=0)


class AssignmentIn(Input):
    waste_report_id: int = Field(gt=0)
    collector_user_id: int | None = None
    scheduled_pickup_at: datetime | None = None
    actual_pickup_at: datetime | None = None
    status: Literal["pending", "assigned", "scheduled", "collected", "cancelled", "failed"] = "pending"
    notes: str | None = None


class BatchIn(Input):
    batch_code: str = Field(min_length=1, max_length=32)
    waste_report_id: int = Field(gt=0)
    waste_type_id: int = Field(gt=0)
    received_quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit: Unit = "kg"
    current_stage: Literal["received", "sorted", "in_processing", "processed", "composted", "reused", "recycled", "rejected"] = "received"
    quality_notes: str | None = None


class ProcessingIn(Input):
    batch_id: int = Field(gt=0)
    processing_partner_user_id: int = Field(gt=0)
    processing_method: Literal["composting", "coir_production", "craft_production", "paper_making", "reuse_upcycling", "authorized_recycling", "sorting", "other"]
    input_quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    input_unit: Unit = "kg"
    output_quantity: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=3)
    output_unit: Unit | None = None
    output_description: str | None = None
    processing_date: datetime
    status: Literal["planned", "in_progress", "completed", "failed"] = "planned"
    evidence_notes: str | None = None

    @model_validator(mode="after")
    def completed_output_is_recorded(self):
        if self.status == "completed" and self.output_quantity is None:
            raise ValueError("completed processing requires an output quantity")
        if self.output_quantity is not None and self.output_unit is None:
            self.output_unit = self.input_unit
        return self


class ArtisanIn(Input):
    user_id: int | None = None
    display_name: str = Field(min_length=1, max_length=160)
    skills: str
    preferred_materials: str
    location: str
    contact_email: str | None = Field(default=None, max_length=254)
    monthly_capacity_kg: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=3)
    availability_status: Literal["available", "busy", "inactive"] = "available"
    contact_visibility: Literal["private", "platform_only", "public"] = "private"

    @field_validator("contact_email")
    @classmethod
    def valid_contact_email(cls, value):
        if value is not None and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("enter a valid contact email address")
        return value.lower() if value else value


class MaterialRequestIn(Input):
    artisan_id: int = Field(gt=0)
    waste_type_id: int = Field(gt=0)
    required_quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit: Unit = "kg"
    request_date: datetime | None = None
    status: Literal["open", "matched", "fulfilled", "cancelled"] = "open"
    notes: str | None = None


class ProductIn(Input):
    artisan_id: int | None = None
    product_name: str = Field(min_length=1, max_length=180)
    description: str
    category: str
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    available_stock: int = Field(ge=0)
    status: Literal["draft", "active", "out_of_stock", "archived"] = "draft"


class ProductBatchIn(Input):
    product_id: int = Field(gt=0)
    batch_id: int = Field(gt=0)
    quantity_used: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit: Unit = "kg"


class OrderUpdateIn(Input):
    status: Literal["pending", "confirmed", "shipped", "completed", "cancelled"]


class OrderItemIn(Input):
    order_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    subtotal: Decimal = Field(ge=0, max_digits=12, decimal_places=2)

    @model_validator(mode="after")
    def subtotal_matches(self):
        if self.subtotal != self.unit_price * self.quantity:
            raise ValueError("subtotal must equal quantity multiplied by unit_price")
        return self


class ImpactIn(Input):
    batch_id: int | None = None
    processing_record_id: int | None = None
    measured_quantity: Decimal = Field(ge=0, max_digits=12, decimal_places=3)
    unit: Unit
    quantity_basis: Literal["reported", "estimated", "processed", "verified"]
    outcome_category: str
    verification_status: Literal["unverified", "evidence_provided", "verified"] = "unverified"
    evidence_reference: str | None = None
    recorded_at: datetime | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def has_target(self):
        if self.batch_id is None and self.processing_record_id is None:
            raise ValueError("impact record must reference a batch or processing record")
        return self


class CheckoutItem(Input):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=99)


class CheckoutIn(Input):
    customer_user_id: int = Field(gt=0)
    items: list[CheckoutItem] = Field(min_length=1, max_length=30)


AnyCreate = UserIn | SourceIn | WasteTypeIn | WasteReportIn | AssignmentIn | BatchIn | ProcessingIn | ArtisanIn | MaterialRequestIn | ProductIn | ProductBatchIn | OrderItemIn | ImpactIn | CheckoutIn


class ResourceOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int


class PageOut(BaseModel):
    items: list[ResourceOut]
    total: int
    limit: int
    offset: int


class HealthOut(BaseModel):
    status: Literal["ok"]
    database: str
    authentication: str


class DashboardOut(BaseModel):
    collected_report_count: int
    recorded_collected_quantity: float
    recorded_processed_quantity: float
    unit: str
    source: str
    demo_records_present: bool
    note: str


class CheckoutOut(BaseModel):
    order: ResourceOut
    items: list[ResourceOut]
    payment: str


CREATE_SCHEMAS = {
    "users": UserIn, "waste-sources": SourceIn, "waste-types": WasteTypeIn,
    "waste-reports": WasteReportIn, "collection-assignments": AssignmentIn,
    "waste-batches": BatchIn, "processing-records": ProcessingIn,
    "artisans": ArtisanIn, "material-requests": MaterialRequestIn,
    "products": ProductIn, "product-batches": ProductBatchIn,
    "orders": CheckoutIn, "order-items": OrderItemIn, "impact-records": ImpactIn,
}
UPDATE_SCHEMAS = {"orders": OrderUpdateIn}
