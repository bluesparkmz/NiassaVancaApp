from auth import get_password_hash
from database import SessionLocal, init_db
from models import User, UserRole


ADMIN_EMAIL = "djoaquimnamueto@gmail.com"


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not user:
            user = User(
                full_name="Admin",
                name="Admin",
                username="admin",
                email=ADMIN_EMAIL,
                phone=None,
                password_hash=get_password_hash("1234"),
                role=UserRole.ADMIN,
                is_admin=True,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created admin user: {user.email} (password=1234)")
        else:
            user.role = UserRole.ADMIN
            user.is_admin = True
            db.commit()
            print(f"Updated user to admin: {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
