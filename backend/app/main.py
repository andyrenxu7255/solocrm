from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_pgvector
from app.ai.router import router as ai_router
from app.domains.agent.router import router as agent_router
from app.domains.business.router import (
    artifact_router,
    business_router,
    engagement_router,
)
from app.domains.case.router import router as case_router
from app.domains.customer.router import router as customer_router
from app.domains.product.router import router as product_router
from app.domains.search.router import router as search_router
from app.domains.todo.router import router as todo_router
from app.domains.visit.router import plan_router, record_router
from app.shared.exceptions import ExternalServiceError, NotFoundError, ValidationError
from app.shared.schemas import APIResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pgvector()
    yield


settings = get_settings()

app = FastAPI(
    title="SoloCRM",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)
app.include_router(agent_router)
app.include_router(business_router)
app.include_router(engagement_router)
app.include_router(artifact_router)
app.include_router(case_router)
app.include_router(customer_router)
app.include_router(plan_router)
app.include_router(record_router)
app.include_router(search_router)
app.include_router(todo_router)
app.include_router(product_router)


@app.get("/health", response_model=APIResponse[str])
async def health():
    return APIResponse.ok("healthy")


@app.exception_handler(NotFoundError)
async def not_found_handler(request, exc: NotFoundError):
    return APIResponse.error(str(exc), code=1)


@app.exception_handler(ValidationError)
async def validation_handler(request, exc: ValidationError):
    return APIResponse.error(str(exc), code=1)


@app.exception_handler(ExternalServiceError)
async def external_service_handler(request, exc: ExternalServiceError):
    return APIResponse.error(str(exc), code=1)
