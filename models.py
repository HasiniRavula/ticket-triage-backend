from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from datetime import datetime

from database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)

    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)

    predicted_queue = Column(String(100), nullable=False)
    predicted_priority = Column(String(50), nullable=False)

    review_required = Column(Boolean, default=False)
    decision_margin = Column(Float, nullable=True)

    status = Column(String(50), default="open")

    final_queue = Column(String(100), nullable=True)
    final_priority = Column(String(50), nullable=True)

    reviewer_note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)