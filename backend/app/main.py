from contextlib import asynccontextmanager
from decimal import Decimal
from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session
from .config import ALLOWED_ORIGINS, PROJECT_DIR
from .database import Base, engine, get_db
from . import models, schemas


RESOURCE_MODELS = {
    "users": models.User, "waste-sources": models.WasteSource,
    "waste-types": models.WasteType, "waste-reports": models.WasteReport,
    "collection-assignments": models.CollectionAssignment, "waste-batches": models.WasteBatch,
    "processing-records": models.ProcessingRecord, "artisans": models.Artisan,
    "material-requests": models.ArtisanMaterialRequest, "products": models.Product,
    "product-batches": models.ProductBatch, "orders": models.CustomerOrder,
    "order-items": models.OrderItem, "impact-records": models.ImpactRecord,
}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Alembic is the supported schema path; create_all keeps first-time SQLite demo use easy.
    if engine.url.get_backend_name() == "sqlite":
        Base.metadata.create_all(engine)
    yield


app = FastAPI(title="PoojaCycle 360 API", version="1.0.0", description="Traceable temple and festival waste-to-value prototype API. Outcomes are reported only when recorded.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Content-Type"])


def safe_row(obj):
    data = {column.key: getattr(obj, column.key) for column in inspect(obj).mapper.column_attrs}
    # Do not publish credentials or private contact fields through unauthenticated CRUD.
    if isinstance(obj, models.User):
        for key in ("password_hash", "email", "phone_number", "location"):
            data.pop(key, None)
    elif isinstance(obj, models.WasteSource):
        data.pop("contact_name", None)
        data.pop("contact_phone", None)
    elif isinstance(obj, models.Artisan) and obj.contact_visibility != "public":
        data.pop("contact_email", None)
    return data


@app.get("/api/health", response_model=schemas.HealthOut)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
        return {"status": "ok", "database": engine.url.get_backend_name(), "authentication": "not implemented"}
    except SQLAlchemyError:
        raise HTTPException(503, "Database is unavailable") from None


@app.get("/api/dashboard", response_model=schemas.DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    # Only explicitly recorded material outcomes appear. No inferred impact multipliers.
    reports = db.execute(select(func.count(models.WasteReport.id), func.coalesce(func.sum(models.WasteReport.quantity), 0)).where(models.WasteReport.collection_status.in_(["collected"]))).one()
    processed = db.execute(select(func.coalesce(func.sum(models.ImpactRecord.measured_quantity), 0)).where(models.ImpactRecord.quantity_basis == "processed")).scalar_one()
    demo_present = db.scalar(select(func.count(models.WasteSource.id)).where(models.WasteSource.source_name.like("DEMO ONLY%"))) > 0
    return {"collected_report_count": reports[0], "recorded_collected_quantity": float(reports[1]), "recorded_processed_quantity": float(processed), "unit": "kg", "source": "database records", "demo_records_present": demo_present, "note": "Seed records are fictional demonstrations; quantities are not independently verified." if demo_present else "Values include only records saved in this database. No environmental savings are inferred."}


@app.post("/api/checkout", status_code=201, response_model=schemas.CheckoutOut)
def checkout(payload: schemas.CheckoutIn, db: Session = Depends(get_db)):
    """Save an order and its line items atomically; payment is simulated only."""
    customer = db.get(models.User, payload.customer_user_id)
    if customer is None or customer.role != "customer":
        raise HTTPException(422, "customer_user_id must reference a customer account")
    try:
        lines, total = [], Decimal("0.00")
        for item in payload.items:
            product = db.get(models.Product, item.product_id)
            if product is None or product.status != "active":
                raise HTTPException(422, f"Product {item.product_id} is not available")
            if product.available_stock < item.quantity:
                raise HTTPException(409, f"Insufficient stock for product {item.product_id}")
            unit_price = Decimal(product.price)
            subtotal = unit_price * item.quantity
            total += subtotal
            lines.append((product, item.quantity, unit_price, subtotal))
        order = models.CustomerOrder(customer_user_id=customer.id, status="pending", total_amount=total, payment_mode="simulated")
        for product, quantity, unit_price, subtotal in lines:
            order.items.append(models.OrderItem(product_id=product.id, quantity=quantity, unit_price=unit_price, subtotal=subtotal))
            product.available_stock -= quantity
            if product.available_stock == 0:
                product.status = "out_of_stock"
        db.add(order)
        db.commit()
        db.refresh(order)
        return {"order": safe_row(order), "items": [safe_row(item) for item in order.items], "payment": "simulated; no payment details collected"}
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Order could not be saved due to a database constraint") from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Order could not be saved") from None


@app.get("/api/{resource}", response_model=schemas.PageOut)
def list_resource(resource: str, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    model = RESOURCE_MODELS.get(resource)
    if model is None:
        raise HTTPException(404, "Resource not found")
    total = db.scalar(select(func.count()).select_from(model)) or 0
    rows = db.scalars(select(model).order_by(model.id).offset(offset).limit(limit)).all()
    return {"items": [safe_row(row) for row in rows], "total": total, "limit": limit, "offset": offset}


@app.post("/api/{resource}", status_code=201, response_model=schemas.ResourceOut)
def create_resource(resource: str, payload: schemas.AnyCreate, db: Session = Depends(get_db)):
    model, schema = RESOURCE_MODELS.get(resource), schemas.CREATE_SCHEMAS.get(resource)
    if model is None or schema is None:
        raise HTTPException(404, "Resource not found")
    try:
        values = schema.model_validate(payload.model_dump()).model_dump(exclude_unset=True, exclude_none=True)
        if resource == "orders":
            return checkout(schemas.CheckoutIn.model_validate(values), db)["order"]
        if resource == "waste-reports":
            reporter = db.get(models.User, values["reported_by_user_id"])
            if reporter is not None and reporter.role not in {"organizer", "admin"}:
                raise HTTPException(422, "reported_by_user_id must reference an organizer or admin")
        if resource == "collection-assignments" and values.get("collector_user_id"):
            collector = db.get(models.User, values["collector_user_id"])
            if collector is not None and collector.role != "collector":
                raise HTTPException(422, "collector_user_id must reference a collector account")
        if resource == "artisans" and values.get("user_id"):
            artisan_user = db.get(models.User, values["user_id"])
            if artisan_user is not None and artisan_user.role != "artisan":
                raise HTTPException(422, "user_id must reference an artisan account")
        if resource == "waste-batches":
            report = db.get(models.WasteReport, values["waste_report_id"])
            if report is not None and (report.collection_status != "collected" or report.waste_type_id != values["waste_type_id"] or values["received_quantity"] > report.quantity or values["unit"] != report.unit):
                raise HTTPException(422, "Batch must match the collected report's waste type, unit, and available quantity")
        if resource == "processing-records":
            partner = db.get(models.User, values["processing_partner_user_id"])
            if partner is not None and partner.role != "processing_partner":
                raise HTTPException(422, "processing_partner_user_id must reference a processing partner account")
            batch = db.get(models.WasteBatch, values["batch_id"])
            if batch is not None:
                waste_type = db.get(models.WasteType, batch.waste_type_id)
                method = values["processing_method"]
                allowed = {
                    "Flowers and leaves": {"composting", "craft_production", "paper_making", "sorting"},
                    "Coconut husks": {"coir_production", "craft_production", "composting", "sorting"},
                    "Coconut shells": {"craft_production", "reuse_upcycling", "sorting"},
                    "Plastic packaging": {"sorting", "authorized_recycling"},
                    "Jute and textile materials": {"craft_production", "reuse_upcycling", "sorting"},
                }
                if method not in allowed.get(waste_type.name, set()):
                    raise HTTPException(422, "Processing method is not configured as suitable for this material type")
                if values["input_quantity"] > batch.received_quantity or values.get("input_unit", "kg") != batch.unit:
                    raise HTTPException(422, "Processing input cannot exceed the tracked batch quantity and must use the batch unit")
        if resource == "product-batches":
            batch = db.get(models.WasteBatch, values["batch_id"])
            product = db.get(models.Product, values["product_id"])
            if batch is not None and (values["quantity_used"] > batch.received_quantity or values["unit"] != batch.unit):
                raise HTTPException(422, "Product provenance amount and unit must fit the tracked batch")
            if product is not None and product.status == "draft":
                raise HTTPException(422, "Only a published product can claim a tracked batch as material provenance")
        if resource == "impact-records":
            if values["quantity_basis"] == "verified" and values["verification_status"] != "verified":
                raise HTTPException(422, "Verified quantity basis requires verified evidence status")
            if values["quantity_basis"] == "processed":
                processing = db.get(models.ProcessingRecord, values.get("processing_record_id")) if values.get("processing_record_id") else None
                if processing is None or processing.status != "completed":
                    raise HTTPException(422, "Processed impact must reference a completed processing record")
        obj = model(**values)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return safe_row(obj)
    except ValidationError as exc:
        raise HTTPException(422, detail=exc.errors(include_url=False)) from None
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Record conflicts with a unique, foreign-key, or database constraint") from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Database operation failed") from None


@app.get("/api/{resource}/{record_id}", response_model=schemas.ResourceOut)
def get_resource(resource: str, record_id: int, db: Session = Depends(get_db)):
    model = RESOURCE_MODELS.get(resource)
    if model is None:
        raise HTTPException(404, "Resource not found")
    obj = db.get(model, record_id)
    if obj is None:
        raise HTTPException(404, "Record not found")
    return safe_row(obj)


@app.patch("/api/{resource}/{record_id}", response_model=schemas.ResourceOut)
def update_resource(resource: str, record_id: int, payload: dict, db: Session = Depends(get_db)):
    model, schema = RESOURCE_MODELS.get(resource), schemas.CREATE_SCHEMAS.get(resource)
    if model is None or schema is None:
        raise HTTPException(404, "Resource not found")
    obj = db.get(model, record_id)
    if obj is None:
        raise HTTPException(404, "Record not found")
    try:
        # Validate against the full stored row (including fields intentionally
        # omitted from API responses, such as a user's email), then return only
        # the privacy-filtered representation.
        current = {column.key: getattr(obj, column.key) for column in inspect(obj).mapper.column_attrs if column.key not in {"id", "created_at", "updated_at"}}
        if isinstance(obj, models.User):
            current.pop("password_hash", None)
        schema = schemas.UPDATE_SCHEMAS.get(resource, schema)
        values = schema.model_validate(payload if resource in schemas.UPDATE_SCHEMAS else {**current, **payload}).model_dump(exclude_unset=True, exclude_none=True)
        if resource == "waste-reports" and "reported_by_user_id" in values:
            reporter = db.get(models.User, values["reported_by_user_id"])
            if reporter is None or reporter.role not in {"organizer", "admin"}:
                raise HTTPException(422, "reported_by_user_id must reference an organizer or admin")
        if resource == "collection-assignments" and values.get("collector_user_id") is not None:
            collector = db.get(models.User, values["collector_user_id"])
            if collector is None or collector.role != "collector":
                raise HTTPException(422, "collector_user_id must reference a collector account")
        if resource == "artisans" and values.get("user_id") is not None:
            artisan_user = db.get(models.User, values["user_id"])
            if artisan_user is None or artisan_user.role != "artisan":
                raise HTTPException(422, "user_id must reference an artisan account")
        for key, value in values.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return safe_row(obj)
    except ValidationError as exc:
        db.rollback()
        raise HTTPException(422, detail=exc.errors(include_url=False)) from None
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Update conflicts with a unique, foreign-key, or database constraint") from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Database operation failed") from None


@app.delete("/api/{resource}/{record_id}", status_code=204)
def delete_resource(resource: str, record_id: int, db: Session = Depends(get_db)):
    model = RESOURCE_MODELS.get(resource)
    if model is None:
        raise HTTPException(404, "Resource not found")
    obj = db.get(model, record_id)
    if obj is None:
        raise HTTPException(404, "Record not found")
    try:
        # A tracked batch is part of the audit trail. Refuse its removal when
        # processing, product provenance, or impact rows refer to it; never
        # silently erase recorded outcomes.
        db.delete(obj)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Record is still referenced and cannot be deleted") from None
    return Response(status_code=204)


# Serve the original responsive prototype and its API adapter from the same origin.
app.mount("/", StaticFiles(directory=str(PROJECT_DIR / "frontend"), html=True), name="frontend")
