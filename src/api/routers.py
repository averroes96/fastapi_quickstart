__all__ = ("register_routers",)
from core.schemas.responses import JSENDResponseSchema
from domain.authorization.dependencies import IsAuthenticated, bearer_auth
from fastapi import APIRouter, Depends, FastAPI, status

from src.api.apps.health_checks.handlers import healthcheck
from src.api.apps.tokens.handlers import login, refresh
from src.api.apps.users.handlers import registration, whoami
from src.api.responses import Responses

API_PREFIX = "/api/v1"


def _health_checks_router() -> APIRouter:
    router = APIRouter(
        prefix="/health",
        tags=["health"],
    )

    router.add_api_route(
        path="/",
        endpoint=healthcheck,
        name="healthcheck",
        summary="Health check.",
        description="Health check endpoint.",
        response_model=JSENDResponseSchema,
        status_code=status.HTTP_200_OK,
    )
    return router


def _users_router() -> APIRouter:
    router = APIRouter(
        prefix="/users",
        tags=["users"],
        dependencies=[Depends(bearer_auth), Depends(IsAuthenticated())],
        responses=Responses.AUTH,
    )

    router.add_api_route(
        path="/",
        endpoint=whoami,
        name="whoami",
        summary="Who am I?",
        description="Get user's data from authorization.",
        status_code=status.HTTP_200_OK,
    )
    return router


def _registration_router() -> APIRouter:
    router = APIRouter(
        prefix="/users",
        tags=["users"],
    )

    router.add_api_route(
        path="/",
        endpoint=registration,
        methods=["POST"],
        name="registration",
        summary="Registration",
        description="Create user and get details.",
        status_code=status.HTTP_201_CREATED,
    )
    return router


def _tokens_router() -> APIRouter:
    router = APIRouter(
        prefix="/tokens",
        tags=["tokens"],
    )

    router.add_api_route(
        path="/refresh/",
        endpoint=refresh,
        methods=["PUT"],
        name="refresh",
    )
    router.add_api_route(
        path="/login/",
        endpoint=login,
        methods=["POST"],
        name="login",
        status_code=status.HTTP_200_OK,
    )
    return router


def _agents_router() -> APIRouter:
    router = APIRouter(
        prefix="/agents",
        tags=["agents"],
    )

    from src.api.apps.agents.handlers import find_wining_product, generate_landing_page

    router.add_api_route(
        path="/winning-product",
        endpoint=find_wining_product,
        methods=["POST"],
        name="find_winning_product",
        summary="Find Winning Product",
        description="Find a winning product based on the provided niche.",
        response_model=JSENDResponseSchema,
        status_code=status.HTTP_200_OK,
    )

    router.add_api_route(
        path="/generate-landing-page",
        endpoint=generate_landing_page,
        methods=["POST"],
        name="generate_landing_page",
        summary="Generate Landing Page",
        description="Generate a landing page for the provided product.",
        response_model=JSENDResponseSchema,
        status_code=status.HTTP_200_OK,
    )

    return router


def register_routers(app: FastAPI) -> None:
    app.include_router(router=_health_checks_router(), prefix=API_PREFIX)
    app.include_router(router=_registration_router(), prefix=API_PREFIX)
    app.include_router(router=_users_router(), prefix=API_PREFIX)
    app.include_router(router=_tokens_router(), prefix=API_PREFIX)
    app.include_router(router=_agents_router(), prefix=API_PREFIX)
