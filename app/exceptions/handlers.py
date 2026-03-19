"""
Exception handlers for dARK Core Admin API.

Maps dark-core-lib exceptions to HTTP responses.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from dark_core_lib.exceptions import (
    AuthorityAlreadyExistsError,
    AuthorityError,
    AuthorityNotFoundError,
    AuthorizationError,
    ConfigurationError,
    DarkCoreError,
    TransactionError,
)

from app.models.responses import ErrorResponse

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""

    @app.exception_handler(AuthorityNotFoundError)
    async def authority_not_found_handler(request: Request, exc: AuthorityNotFoundError):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="AUTHORITY_NOT_FOUND",
                message=str(exc),
                retryable=False,
            ).model_dump(),
        )

    @app.exception_handler(AuthorityAlreadyExistsError)
    async def authority_exists_handler(request: Request, exc: AuthorityAlreadyExistsError):
        return JSONResponse(
            status_code=409,
            content=ErrorResponse(
                error="AUTHORITY_ALREADY_EXISTS",
                message=str(exc),
                retryable=False,
            ).model_dump(),
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(
            status_code=403,
            content=ErrorResponse(
                error="AUTHORIZATION_FAILED",
                message=str(exc),
                retryable=False,
            ).model_dump(),
        )

    @app.exception_handler(AuthorityError)
    async def authority_error_handler(request: Request, exc: AuthorityError):
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="AUTHORITY_ERROR",
                message=str(exc),
                retryable=False,
            ).model_dump(),
        )

    @app.exception_handler(TransactionError)
    async def transaction_error_handler(request: Request, exc: TransactionError):
        logger.error(f"Transaction error: {exc}")

        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error="BLOCKCHAIN_ERROR",
                message=str(exc),
                retryable=True,
                details={
                    "tx_hash": getattr(exc, "tx_hash", None),
                    "gas_used": getattr(exc, "gas_used", None),
                },
            ).model_dump(),
        )

    @app.exception_handler(ConfigurationError)
    async def configuration_error_handler(request: Request, exc: ConfigurationError):
        logger.error(f"Configuration error: {exc}")

        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="CONFIGURATION_ERROR",
                message="Internal configuration error",
                retryable=False,
            ).model_dump(),
        )

    @app.exception_handler(DarkCoreError)
    async def dark_core_error_handler(request: Request, exc: DarkCoreError):
        logger.error(f"dark-core-lib error: {exc}")

        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="INTERNAL_ERROR",
                message=str(exc),
                retryable=False,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unexpected error: {exc}")

        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="INTERNAL_ERROR",
                message="An unexpected error occurred",
                retryable=False,
            ).model_dump(),
        )
