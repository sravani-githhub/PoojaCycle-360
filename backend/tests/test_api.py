from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app import main, schemas
from app.seed_demo import seed_demo


class EndpointHarness:
    """Invoke the same FastAPI endpoint handlers using an isolated test session."""
    def __init__(self, db): self.db = db
    def get(self, resource, record_id=None):
        return main.list_resource(resource, 50, 0, self.db) if record_id is None else main.get_resource(resource, record_id, self.db)
    def post(self, resource, schema): return main.create_resource(resource, schema, self.db)
    def patch(self, resource, record_id, payload): return main.update_resource(resource, record_id, payload, self.db)
    def delete(self, resource, record_id): return main.delete_resource(resource, record_id, self.db)


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    @event.listens_for(engine, "connect")
    def fk_on(conn, _record):
        conn.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
    with TestingSession() as db:
        seed_demo(db)
        yield EndpointHarness(db)
    engine.dispose()


def test_health_and_demo_seed_are_real_database_rows(client):
    assert main.health(client.db)["status"] == "ok"
    assert client.get("waste-types")["total"] == 5
    assert client.get("artisans")["total"] == 3


def test_create_and_read_waste_report(client):
    source = client.get("waste-sources")["items"][0]
    waste_type = client.get("waste-types")["items"][0]
    organizer = next(user for user in client.get("users")["items"] if user["role"] == "organizer")
    payload = {"source_id": source["id"], "waste_type_id": waste_type["id"], "quantity": "2.500", "unit": "kg", "availability_at": datetime.now(timezone.utc).isoformat(), "reported_by_user_id": organizer["id"]}
    created = client.post("waste-reports", schemas.WasteReportIn(**payload))
    assert created["id"] > 0
    assert str(client.get("waste-reports", created["id"])["quantity"]) == "2.500"


def test_invalid_quantity_status_and_foreign_key_rejected(client):
    common = {"source_id": 99999, "waste_type_id": 1, "availability_at": datetime.now(timezone.utc).isoformat(), "reported_by_user_id": 1}
    with pytest.raises(ValidationError): schemas.WasteReportIn(**{**common, "quantity": 0})
    with pytest.raises(ValidationError): schemas.WasteReportIn(**{**common, "quantity": 2, "collection_status": "invented"})
    with pytest.raises(HTTPException) as error:
        client.post("waste-reports", schemas.WasteReportIn(**{**common, "quantity": 2}))
    assert getattr(error.value, "status_code", None) == 409


def test_order_item_subtotal_validation(client):
    with pytest.raises(ValidationError):
        schemas.OrderItemIn(order_id=1, product_id=1, quantity=2, unit_price="10.00", subtotal="19.00")


def test_source_crud(client):
    created = client.post("waste-sources", schemas.SourceIn(source_name="Temporary demo source", source_type="festival", address="Fictional address"))
    changed = client.patch("waste-sources", created["id"], {"source_name": "Updated demo source"})
    assert changed["source_name"] == "Updated demo source"
    assert client.delete("waste-sources", created["id"]).status_code == 204


def test_checkout_saves_order_and_price_snapshot(client):
    customer = next(user for user in client.get("users")["items"] if user["role"] == "customer")
    product = client.get("products")["items"][0]
    initial_stock = product["available_stock"]
    result = main.checkout(schemas.CheckoutIn(customer_user_id=customer["id"], items=[{"product_id": product["id"], "quantity": 2}]), client.db)
    assert result["order"]["total_amount"] == product["price"] * 2
    assert len(result["items"]) == 1
    assert client.get("products", product["id"])["available_stock"] == initial_stock - 2
