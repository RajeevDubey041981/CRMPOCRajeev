"""One-time backfill for user_pending_actions from current workflow state."""

from app.database import SessionLocal
from app.services.pending_action_sync import backfill_all_pending_actions


def main() -> None:
    db = SessionLocal()
    try:
        counts = backfill_all_pending_actions(db)
        db.commit()
        print("[backfill_pending_actions]", counts)
    finally:
        db.close()


if __name__ == "__main__":
    main()
