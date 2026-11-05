from sqlalchemy.orm import Session

from app.models.message import Message


def get_user_messages(db: Session, user_id: int) -> list[Message]:
    """Return a user's messages oldest first, ready to build a prompt."""
    return (
        db.query(Message)
        .filter(Message.user_id == user_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )
