from pydantic import BaseModel, Field


class TicketRequest(BaseModel):

    subject: str = Field(
        ...,
        min_length=1,
        description="Customer support ticket subject"
    )

    body: str = Field(
        ...,
        min_length=1,
        description="Customer support ticket body"
    )


class Explanation(BaseModel):

    queue_terms: list[str]

    priority_terms: list[str]


class PredictionResponse(BaseModel):

    queue: str

    priority: str

    review_required: bool

    decision_margin: float

    explanation: Explanation
class ReviewRequest(BaseModel):
    final_queue: str = Field(..., min_length=1)
    final_priority: str = Field(..., min_length=1)
    reviewer_note: str = ""