from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Comentario: configuracao basica do banco usando SQLite para ambiente local.
DATABASE_URL = "sqlite:///./meuchat.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    # Comentario: dependency do FastAPI para abrir/fechar sessoes do banco.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
