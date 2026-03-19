"""
Admin endpoints for Authority management.

Provides administrative operations for managing authorities in the dARK network.
"""

import logging

from fastapi import APIRouter, Depends, Path

from dark_core_lib import DARKCoreClient

from app.config import get_settings
from app.dependencies import get_corelib_client
from app.middleware.auth import require_mtls
from app.models.requests import (
    AuthorizeNAANRequest,
    FundWalletRequest,
    RegisterAuthorityRequest,
    RevokeNAANRequest,
)
from app.models.responses import (
    AdminStatusResponse,
    AuthorityResponse,
    BalanceResponse,
    OperationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _tx_hash_or_none(tx_hash: str) -> str | None:
    """Normalize empty transaction hashes to ``None`` for API responses."""
    return tx_hash or None


@router.post(
    "/authority",
    response_model=AuthorityResponse,
    summary="Register a new authority",
    description=(
        "Creates a new authority with wallet, registers on blockchain, and authorizes NAANs. "
        "This is the main operation to onboard a new authority to the dARK network."
    ),
)
async def register_authority(
    request: RegisterAuthorityRequest,
    cert_info: dict = Depends(require_mtls),
    corelib_client: DARKCoreClient = Depends(get_corelib_client),
) -> AuthorityResponse:
    """
    Register a new authority.

    This operation:
    1. Creates a new wallet for the authority
    2. Encrypts and stores the private key on blockchain
    3. Funds the wallet from admin account
    4. Registers the authority on blockchain
    5. Authorizes all specified NAANs
    """
    logger.info(f"Registering new authority: {request.uuid} with NAANs: {request.naans}")

    settings = get_settings()

    if request.fund_amount_eth is not None:
        fund_amount_wei = corelib_client.w3.to_wei(request.fund_amount_eth, "ether")
    else:
        fund_amount_wei = corelib_client.w3.to_wei(settings.default_fund_amount_eth, "ether")

    authority = corelib_client.setup_authority(
        uuid=request.uuid,
        naans=request.naans,
        fund_amount_wei=fund_amount_wei,
    )
    balance = corelib_client.get_wallet_balance(request.uuid)

    logger.info(f"Authority {request.uuid} registered successfully")

    return AuthorityResponse(
        uuid=authority.uuid,
        wallet_address=authority.wallet_address,
        naans=authority.naans,
        active=authority.active,
        balance_eth=balance,
    )


@router.get(
    "/authority/{uuid}",
    response_model=AuthorityResponse,
    summary="Get authority info",
    description="Get information about a registered authority including wallet address and balance.",
)
async def get_authority(
    uuid: str = Path(..., description="Authority UUID"),
    cert_info: dict = Depends(require_mtls),
    corelib_client: DARKCoreClient = Depends(get_corelib_client),
) -> AuthorityResponse:
    """Get authority information by UUID."""
    logger.info(f"Getting authority: {uuid}")

    authority = corelib_client.get_authority_by_uuid(uuid)
    balance = corelib_client.get_wallet_balance(uuid)

    return AuthorityResponse(
        uuid=authority.uuid,
        wallet_address=authority.wallet_address,
        naans=authority.naans,
        active=authority.active,
        balance_eth=balance,
    )


@router.post(
    "/authority/{uuid}/authorize-naan",
    response_model=OperationResponse,
    summary="Authorize NAAN for authority",
    description="Authorize an additional NAAN for an existing authority.",
)
async def authorize_naan(
    request: AuthorizeNAANRequest,
    uuid: str = Path(..., description="Authority UUID"),
    cert_info: dict = Depends(require_mtls),
    corelib_client: DARKCoreClient = Depends(get_corelib_client),
) -> OperationResponse:
    """Authorize a NAAN for an authority."""
    logger.info(f"Authorizing NAAN {request.naan} for authority {uuid}")

    authority = corelib_client.get_authority_by_uuid(uuid)
    if request.naan in authority.naans:
        return OperationResponse(
            status="success",
            message=f"NAAN {request.naan} was already authorized for {uuid}",
            transaction_hash=None,
        )

    receipt = corelib_client.authorize_naan(uuid, request.naan)
    return OperationResponse(
        status="success",
        message=f"NAAN {request.naan} authorized for {uuid}",
        transaction_hash=_tx_hash_or_none(receipt.tx_hash),
    )


@router.post(
    "/authority/{uuid}/revoke-naan",
    response_model=OperationResponse,
    summary="Revoke NAAN from authority",
    description="Revoke a NAAN authorization from an existing authority.",
)
async def revoke_naan(
    request: RevokeNAANRequest,
    uuid: str = Path(..., description="Authority UUID"),
    cert_info: dict = Depends(require_mtls),
    corelib_client: DARKCoreClient = Depends(get_corelib_client),
) -> OperationResponse:
    """Revoke a NAAN from an authority."""
    logger.info(f"Revoking NAAN {request.naan} from authority {uuid}")

    authority = corelib_client.get_authority_by_uuid(uuid)
    if request.naan not in authority.naans:
        return OperationResponse(
            status="success",
            message=f"NAAN {request.naan} was not authorized for {uuid}",
            transaction_hash=None,
        )

    receipt = corelib_client.revoke_naan(uuid, request.naan)
    return OperationResponse(
        status="success",
        message=f"NAAN {request.naan} revoked for {uuid}",
        transaction_hash=_tx_hash_or_none(receipt.tx_hash),
    )


@router.post(
    "/authority/{uuid}/deactivate",
    response_model=OperationResponse,
    summary="Deactivate authority",
    description="Deactivate an authority, preventing it from minting new ARKs.",
)
async def deactivate_authority(
    uuid: str = Path(..., description="Authority UUID"),
    cert_info: dict = Depends(require_mtls),
    corelib_client: DARKCoreClient = Depends(get_corelib_client),
) -> OperationResponse:
    """Deactivate an authority."""
    logger.info(f"Deactivating authority: {uuid}")

    authority = corelib_client.get_authority_by_uuid(uuid)
    if not authority.active:
        return OperationResponse(
            status="success",
            message=f"Authority {uuid} is already inactive",
            transaction_hash=None,
        )

    receipt = corelib_client.deactivate_authority(uuid)
    return OperationResponse(
        status="success",
        message=f"Authority {uuid} deactivated",
        transaction_hash=_tx_hash_or_none(receipt.tx_hash),
    )


@router.get(
    "/authority/{uuid}/balance",
    response_model=BalanceResponse,
    summary="Get wallet balance",
    description="Get the wallet balance for an authority.",
)
async def get_balance(
    uuid: str = Path(..., description="Authority UUID"),
    cert_info: dict = Depends(require_mtls),
    corelib_client: DARKCoreClient = Depends(get_corelib_client),
) -> BalanceResponse:
    """Get wallet balance for an authority."""
    logger.info(f"Getting balance for authority: {uuid}")

    authority = corelib_client.get_authority_by_uuid(uuid)
    balance = corelib_client.get_wallet_balance(uuid)

    return BalanceResponse(
        uuid=uuid,
        wallet_address=authority.wallet_address,
        balance_eth=balance,
    )


@router.post(
    "/authority/{uuid}/fund",
    response_model=OperationResponse,
    summary="Fund authority wallet",
    description="Send ETH to an authority's wallet from the admin account.",
)
async def fund_wallet(
    request: FundWalletRequest,
    uuid: str = Path(..., description="Authority UUID"),
    cert_info: dict = Depends(require_mtls),
    corelib_client: DARKCoreClient = Depends(get_corelib_client),
) -> OperationResponse:
    """Fund an authority wallet."""
    logger.info(f"Funding authority {uuid} with {request.amount_eth} ETH")

    corelib_client.get_authority_by_uuid(uuid)
    amount_wei = corelib_client.w3.to_wei(request.amount_eth, "ether")
    receipt = corelib_client.fund_authority_wallet(uuid, amount_wei)

    return OperationResponse(
        status="success",
        message=f"Funded {uuid} with {request.amount_eth} ETH",
        transaction_hash=_tx_hash_or_none(receipt.tx_hash),
    )


@router.get(
    "/status",
    response_model=AdminStatusResponse,
    summary="Get admin status",
    description="Get system status including admin account info and blockchain connection.",
)
async def get_status(
    cert_info: dict = Depends(require_mtls),
    corelib_client: DARKCoreClient = Depends(get_corelib_client),
) -> AdminStatusResponse:
    """Get admin status and system information."""
    logger.info("Getting admin status")

    return AdminStatusResponse(
        admin_address=corelib_client.admin_account.address,
        admin_balance_eth=corelib_client.get_admin_balance(),
        blockchain_connected=corelib_client.is_connected(),
        current_block=corelib_client.get_block_number(),
        chain_id=corelib_client.config.chain_id,
    )
