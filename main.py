import os
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import Ticket
from schemas import (
    TicketRequest,
    PredictionResponse,
    ReviewRequest
)
from predictor import predict_ticket

# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)

# Initialize single FastAPI instance
app = FastAPI(
    title="SmartDesk AI",
    description="AI-powered customer support ticket triage system",
    version="1.0.0"
)

# Enable CORS for all origins (eliminates frontend blocking)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ============================================================
# ROOT / DASHBOARD SERVING
# ============================================================

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    """Serves the dashboard directly when opening http://127.0.0.1:8000"""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "index.html"),
        os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html"),
        os.path.join(os.path.dirname(__file__), "..", "index.html")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

    return """
    <html>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
            <h2>SmartDesk AI Backend is running!</h2>
            <p>Place <code>index.html</code> in your <code>backend</code> or <code>frontend</code> folder to load the dashboard.</p>
            <p><a href="/docs">View API Documentation (Swagger)</a></p>
        </body>
    </html>
    """

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "SmartDesk AI"
    }

# ============================================================
# TICKET ENDPOINTS
# ============================================================

@app.post("/tickets")
def create_ticket(
    ticket: TicketRequest,
    db: Session = Depends(get_db)
):
    prediction = predict_ticket(
        ticket.subject,
        ticket.body
    )

    new_ticket = Ticket(
        subject=ticket.subject,
        body=ticket.body,
        predicted_queue=prediction["queue"],
        predicted_priority=prediction["priority"],
        review_required=prediction["review_required"],
        decision_margin=prediction.get("decision_margin", 0.0),
        status="open"
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket


@app.get("/tickets")
def get_tickets(db: Session = Depends(get_db)):
    return db.query(Ticket).order_by(Ticket.created_at.desc()).all()


@app.get("/tickets/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )
    return ticket


@app.post("/review/{ticket_id}")
def review_ticket(
    ticket_id: int,
    review: ReviewRequest,
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    ticket.final_queue = review.final_queue
    ticket.final_priority = review.final_priority
    ticket.reviewer_note = review.reviewer_note
    ticket.reviewed_at = datetime.utcnow()
    ticket.status = "reviewed"
    ticket.review_required = False

    db.commit()
    db.refresh(ticket)

    return {
        "message": "Ticket reviewed successfully",
        "ticket_id": ticket.id,
        "final_queue": ticket.final_queue,
        "final_priority": ticket.final_priority,
        "status": ticket.status,
        "reviewer_note": ticket.reviewer_note
    }


# ============================================================
# ANALYTICS ENDPOINT
# ============================================================

@app.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    tickets = db.query(Ticket).all()
    total_tickets = len(tickets)

    open_tickets = sum(1 for t in tickets if t.status == "open")
    reviewed_tickets = sum(1 for t in tickets if t.status == "reviewed")
    review_required = sum(1 for t in tickets if t.review_required)

    queue_distribution = {}
    for t in tickets:
        q = t.predicted_queue or "Unassigned"
        queue_distribution[q] = queue_distribution.get(q, 0) + 1

    priority_distribution = {}
    for t in tickets:
        p = t.predicted_priority or "Normal"
        priority_distribution[p] = priority_distribution.get(p, 0) + 1

    review_rate = (reviewed_tickets / total_tickets * 100) if total_tickets > 0 else 0

    return {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "reviewed_tickets": reviewed_tickets,
        "review_required": review_required,
        "review_rate": round(review_rate, 2),
        "queue_distribution": queue_distribution,
        "priority_distribution": priority_distribution
    }