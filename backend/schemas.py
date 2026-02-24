from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# =====================================================
# Request Model
# =====================================================



class OrchestrateRequest(BaseModel):
    session_id: str = Field(
        ...,
        description="Unique session identifier"
    )

    question: Optional[str] = Field(
        default=None,
        description="Optional user-provided question"
    )

    conversation: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Conversation history for contextual orchestration"
    )

    num_competitors: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Number of competitor models (1– 5)"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.5,
        description="Model temperature (0.0–1.5)"
    )



# Response Models


class LatencyBreakdown(BaseModel):
    question_generation_sec: float
    competitor_generation_sec: float
    judge_sec: float
    total_sec: float


class OrchestrateResponse(BaseModel):
    question: str
    competitors: List[str]
    answers: List[str]
    ranking: List[int]
    latency: LatencyBreakdown
