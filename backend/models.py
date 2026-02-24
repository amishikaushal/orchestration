from beanie import Document
from pydantic import Field
from datetime import datetime



class User(Document):
    email: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"


from beanie import Document
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import Field


class OrchestrationRun(Document):
    user_id: str
    session_id: str

    question: str
    competitors: List[str]
    answers: List[str]
    ranking: List[int]

    latency: Dict[str, Any]
    judge_model: str
    latency_ms: float

    conversation: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "orchestration_runs"
