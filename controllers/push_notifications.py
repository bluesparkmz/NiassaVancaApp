import requests
from sqlalchemy.orm import Session

import models


EXPO_PUSH_ENDPOINT = "https://exp.host/--/api/v2/push/send"


def is_expo_push_token(token: str | None) -> bool:
    if not token:
        return False
    # Comentario: aceita formatos usados pelo Expo Push Service.
    return token.startswith("ExponentPushToken[") or token.startswith("ExpoPushToken[")


def send_expo_push(
    *,
    to_token: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> bool:
    if not is_expo_push_token(to_token):
        return False

    payload = {
        "to": to_token,
        "title": title,
        "body": body,
        "sound": "default",
        "data": data or {},
        "priority": "high",
    }
    try:
        response = requests.post(
            EXPO_PUSH_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        return response.status_code < 400
    except Exception:
        return False


def get_user_push_tokens(
    db: Session,
    user_id: int,
    legacy_token: str | None = None,
) -> list[str]:
    tokens: set[str] = set()
    app_android_package = "com.bluesparkmz.meuchat"

    device_rows = (
        db.query(models.PushDevice.token, models.PushDevice.platform)
        .filter(models.PushDevice.user_id == user_id)
        .all()
    )
    for row in device_rows:
        token = row[0]
        platform = row[1] or ""
        # Comentario: envia push apenas para build standalone do app oficial.
        if "standalone" not in platform:
            continue
        if app_android_package not in platform:
            continue
        if is_expo_push_token(token):
            tokens.add(token)

    return list(tokens)
