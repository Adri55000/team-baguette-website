from app.infrastructure.database.database import SessionLocal
from app.modules.auth.service import cleanup_expired_sessions


def main() -> None:
    with SessionLocal() as db:
        try:
            deleted_count = cleanup_expired_sessions(db)
            db.commit()

            print(
                f"Nettoyage termine : "
                f"{deleted_count} session(s) expiree(s) supprimee(s)"
            )

        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    main()
