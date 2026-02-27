import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.api.deps import get_db
from app.db.base import Base  # tu Declarative Base

# SQLite en memoria para tests
TEST_DATABASE_URL = "postgresql+psycopg://postgres:postgres@db:5432/hookshot_test"

engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    # Importa modelos para que Base.metadata los vea
    from app.models.subscription import Subscription
    from app.models.event import EventPayload
    from app.models.delivery_attempt import DeliveryAttempt

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def override_get_db(db_session):
    def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture()
async def client(override_get_db):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac