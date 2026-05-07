import os

from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL nao definido")

is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    pool_pre_ping=not is_sqlite,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    company_columns = {column["name"] for column in inspector.get_columns("companies")}
    if "gallery_images" not in company_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE companies ADD COLUMN gallery_images JSON"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
