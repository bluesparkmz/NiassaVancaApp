import sys
from pathlib import Path

from fastapi import FastAPI

# Comentario: estilo SkyVenda sem pacote.
app_dir = Path(__file__).resolve().parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from database import engine  # noqa: E402
from models import Base  # noqa: E402
from routers.user import router as user_router  # noqa: E402
from routers.messages import router as messages_router  # noqa: E402
from routers.websoket_router import router as websoket_router  # noqa: E402

app = FastAPI(title="MeuChat")

# Comentario: cria tabelas no startup (para prototipo).
Base.metadata.create_all(bind=engine)

app.include_router(user_router)
app.include_router(messages_router)
app.include_router(websoket_router)
