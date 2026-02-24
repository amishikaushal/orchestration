import logging
import time
import uuid
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, EmailStr

from backend.ai_orchestrator import run_orchestration
from backend.schemas import OrchestrateRequest, OrchestrateResponse
from backend.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

from backend.db import init_db
from backend.models import OrchestrationRun, User
from backend.exceptions import (
    AppException,
    AuthenticationError,
    ValidationError
)

# ---------------------------------------------------
# Logging Setup
# ---------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------
# FastAPI App
# ---------------------------------------------------

app = FastAPI(
    title="AI Orchestration Service",
    description="Runs multi-LLM orchestration and judging",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# Global Exception Handlers
# ---------------------------------------------------

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.error({
        "event": "app_exception",
        "error_code": exc.error_code,
        "message": exc.message,
        "path": str(request.url)
    })

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.error_code,
            "message": exc.message
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error({
        "event": "request_validation_error",
        "details": exc.errors(),
        "path": str(request.url)
    })

    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error_code": "REQUEST_VALIDATION_ERROR",
            "message": "Invalid request payload"
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception({
        "event": "unhandled_exception",
        "path": str(request.url)
    })

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong"
        }
    )

# ---------------------------------------------------
# DB INIT ON STARTUP
# ---------------------------------------------------

@app.on_event("startup")
async def app_init():
    await init_db()

# ---------------------------------------------------
# Schemas
# ---------------------------------------------------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

# ---------------------------------------------------
# Health Check
# ---------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ---------------------------------------------------
# AUTH: Signup
# ---------------------------------------------------

@app.post("/signup")
async def signup(data: SignupRequest):
    existing_user = await User.find_one(User.email == data.email)

    if existing_user:
        raise ValidationError("User already exists")

    hashed_password = get_password_hash(data.password)

    new_user = User(
        email=data.email,
        hashed_password=hashed_password
    )

    await new_user.insert()

    return {"message": "User created successfully"}

# ---------------------------------------------------
# AUTH: Login
# ---------------------------------------------------

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        raise AuthenticationError("Incorrect email or password")

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ---------------------------------------------------
# Protected Orchestration Endpoint
# ---------------------------------------------------

@app.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(
    request: OrchestrateRequest,
    current_user: str = Depends(get_current_user)
):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    logger.info({
        "event": "orchestration_started",
        "request_id": request_id,
        "user": current_user,
        "session_id": request.session_id
    })

    # Run orchestration
    result: OrchestrateResponse = await run_orchestration(request)

    total_time = round(time.time() - start_time, 3)

    # Persist run
    run = OrchestrationRun(
        user_id=current_user,
        session_id=request.session_id,
        question=result["question"],
        competitors=result["competitors"],
        answers=result["answers"],
        ranking=result["ranking"],
        latency=result["latency"],
        conversation=result.get("conversation", []),
        judge_model="llama3.2",
        latency_ms=total_time * 1000,
        created_at=datetime.utcnow()
    )

    await run.insert()

    logger.info({
        "event": "orchestration_completed",
        "request_id": request_id,
        "latency_ms": total_time * 1000
    })

    return result
