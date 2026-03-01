from fastapi import FastAPI

from .database import Base, engine
from .routers import user as user_router
from .routers import messages as messages_router
from .routers import websoket_router

app = FastAPI(title="MeuChat")

# Comentario: cria tabelas no startup (para prototipo).
Base.metadata.create_all(bind=engine)

app.include_router(user_router.router)
app.include_router(messages_router.router)
app.include_router(websoket_router.router)
