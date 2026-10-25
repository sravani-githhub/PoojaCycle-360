"""Insert fictional, visibly labelled demo records; safe to run more than once."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select
from app.database import SessionLocal
from app.models import User, WasteSource, WasteType, WasteReport, Artisan, Product, WasteBatch, ProcessingRecord, ImpactRecord

DEMO_TYPES = [
    ("Flowers and leaves", "Organic floral and leaf material.", "Keep dry matter separate from mixed waste; remove string, foil, and plastic."),
    ("Coconut husks", "Fibrous outer coconut husk.", "Store dry and separate from shells and general waste."),
    ("Coconut shells", "Hard shell material from coconuts.", "Keep clean and dry; reuse suitability depends on condition."),
    ("Plastic packaging", "Mixed packaging that needs identification and sorting.", "Do not assume it is recyclable. Confirm polymer, local acceptance, and authorized route first."),
    ("Jute and textile materials", "Jute sacks, cloth, and suitable textile offcuts.", "Keep dry and separate from contaminated materials."),
]


def seed_demo(db):
    users = {}
    for full_name, email, role, location in [
        ("DEMO ONLY — Platform Admin", "admin@example.invalid", "admin", "Hyderabad (sample)"),
        ("DEMO ONLY — Temple Organizer", "organizer@example.invalid", "organizer", "Hyderabad (sample)"),
        ("DEMO ONLY — Collector", "collector@example.invalid", "collector", "Hyderabad (sample)"),
        ("DEMO ONLY — Processing Partner", "processor@example.invalid", "processing_partner", "Hyderabad (sample)"),
        ("DEMO ONLY — Customer", "customer@example.invalid", "customer", "Hyderabad (sample)"),
    ]:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(full_name=full_name, email=email, role=role, location=location, password_hash=None)
            db.add(user)
            db.flush()
        users[role] = user

    types = {}
    for name, description, notes in DEMO_TYPES:
        item = db.scalar(select(WasteType).where(WasteType.name == name))
        if item is None:
            item = WasteType(name=name, description=description, handling_notes=notes)
            db.add(item)
            db.flush()
        types[name] = item

    source = db.scalar(select(WasteSource).where(WasteSource.source_name == "DEMO ONLY — Sample Temple"))
    if source is None:
        source = WasteSource(source_name="DEMO ONLY — Sample Temple", source_type="temple", address="Fictional sample address, Hyderabad", contact_name="Sample Contact")
        db.add(source)
        db.flush()

    report = db.scalar(select(WasteReport).where(WasteReport.contamination_notes == "Seeded fictional sample record; not verified."))
    if report is None:
        report = WasteReport(source_id=source.id, waste_type_id=types["Flowers and leaves"].id, quantity=Decimal("12.000"), unit="kg", contamination_level=Decimal("0.00"), contamination_notes="Seeded fictional sample record; not verified.", availability_at=datetime.now(timezone.utc) - timedelta(days=1), collection_status="collected", reported_by_user_id=users["organizer"].id)
        db.add(report)
        db.flush()
        batch = WasteBatch(batch_code="DEMO-BATCH-001", waste_report_id=report.id, waste_type_id=report.waste_type_id, received_quantity=report.quantity, unit="kg", current_stage="processed", quality_notes="DEMO ONLY — sample tracking data, not an independently verified outcome.")
        db.add(batch)
        db.flush()
        processing = ProcessingRecord(batch_id=batch.id, processing_partner_user_id=users["processing_partner"].id, processing_method="composting", input_quantity=Decimal("12.000"), input_unit="kg", output_quantity=Decimal("4.000"), output_unit="kg", output_description="Fictional sample compost output", processing_date=datetime.now(timezone.utc), status="completed", evidence_notes="DEMO ONLY — demonstration record; no evidence attached.")
        db.add(processing)
        db.flush()
        db.add(ImpactRecord(processing_record_id=processing.id, measured_quantity=Decimal("4.000"), unit="kg", quantity_basis="processed", outcome_category="compost_output", verification_status="unverified", notes="DEMO ONLY — recorded sample output; not verified."))

    demo_artisans = {}
    for name, skill, material in [
        ("DEMO ONLY — Lakshmi Crafts Collective", "Paper craft, bookmarks", "Flowers and leaves"),
        ("DEMO ONLY — Shell and Fibre Studio", "Coir and shell craft", "Coconut husks; Coconut shells"),
        ("DEMO ONLY — Jute Stitch Group", "Textile repair and reusable bags", "Jute and textile materials"),
    ]:
        if db.scalar(select(Artisan).where(Artisan.display_name == name)) is None:
            artisan = Artisan(display_name=name, skills=skill, preferred_materials=material, location="Hyderabad (sample)", availability_status="available", contact_visibility="private")
            db.add(artisan)
            db.flush()
        else:
            artisan = db.scalar(select(Artisan).where(Artisan.display_name == name))
        demo_artisans[name] = artisan

    demo_products = [
        (1, "DEMO ONLY — Flower-based greeting card set", "flower", 249, "Temple marigold and rose petals", "DEMO ONLY — Lakshmi Crafts Collective"),
        (2, "DEMO ONLY — Plantable bookmarks (pack of 5)", "flower", 179, "Seed paper from temple flowers", "DEMO ONLY — Lakshmi Crafts Collective"),
        (3, "DEMO ONLY — Coconut-shell pen stand", "coconut", 329, "Reclaimed coconut shell", "DEMO ONLY — Shell and Fibre Studio"),
        (4, "DEMO ONLY — Coconut-shell decorative lamp", "coconut", 799, "Reclaimed coconut shell", "DEMO ONLY — Shell and Fibre Studio"),
        (5, "DEMO ONLY — Coir doormat and crafts", "coconut", 459, "Coconut husk fibre", "DEMO ONLY — Shell and Fibre Studio"),
        (6, "DEMO ONLY — Reusable jute gift bag", "jute", 199, "Jute and reclaimed cotton", "DEMO ONLY — Jute Stitch Group"),
    ]
    for product_id, name, category, price, description, artisan_name in demo_products:
        if db.get(Product, product_id) is None:
            db.add(Product(id=product_id, artisan_id=demo_artisans[artisan_name].id, product_name=name, description=description, category=category, price=Decimal(price), available_stock=5, status="active"))
    db.commit()


if __name__ == "__main__":
    with SessionLocal() as session:
        seed_demo(session)
    print("Fictional DEMO ONLY sample records inserted (or already present).")
