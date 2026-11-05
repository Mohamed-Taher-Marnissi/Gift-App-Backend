from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, Enum 
from sqlalchemy.sql import func

from app.database import Base
from app.enums.message_role import MessageRole


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    role = Column(
        Enum(MessageRole, name="message_role"),
        nullable=False
    )

    content = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
