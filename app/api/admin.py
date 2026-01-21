"""
Admin endpoints for Authority management.

Provides administrative operations for managing authorities in the dARK network.
"""

import logging
from fastapi import APIRouter, Depends, Path, HTTPException

from dark_orchestrator import DARKOrchestrator
from dark_orchestrator.exceptions import AuthorityError, DARKError

from app.config import get_settings
from app.dependencies import get_orchestrator
from app.middleware.auth import require_mtls
from app.models.requests import (
    RegisterAuthorityRequest,
    AuthorizeNAANRequest,
    RevokeNAANRequest,
    FundWalletRequest,
)
from app.models.responses import (
    AuthorityResponse,
    BalanceResponse,
    OperationResponse,
    AdminStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Authority Management
# =============================================================================

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
    orchestrator: DARKOrchestrator = Depends(get_orchestrator),
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
    
    # Calculate funding amount
    if request.fund_amount_eth is not None:
        fund_amount_wei = orchestrator.w3.to_wei(request.fund_amount_eth, "ether")
    else:
        fund_amount_wei = orchestrator.w3.to_wei(settings.default_fund_amount_eth, "ether")
    
    # Setup authority (creates wallet, registers, authorizes NAANs)
    authority = orchestrator.setup_authority(
        uuid=request.uuid,
        naans=request.naans,
        fund_amount_wei=fund_amount_wei,
    )
    
    # Get wallet balance
    balance = orchestrator.get_wallet_balance(request.uuid)
    
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
    orchestrator: DARKOrchestrator = Depends(get_orchestrator),
) -> AuthorityResponse:
    """
    Get authority information by UUID.
    """
    logger.info(f"Getting authority: {uuid}")
    
    authority = orchestrator.get_authority_by_uuid(uuid)
    balance = orchestrator.get_wallet_balance(uuid)
    
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
    orchestrator: DARKOrchestrator = Depends(get_orchestrator),
) -> OperationResponse:
    """
    Authorize a NAAN for an authority.
    """
    logger.info(f"Authorizing NAAN {request.naan} for authority {uuid}")
    
    # Get authority credentials
    authority = orchestrator.get_authority_by_uuid(uuid)
    wallet_address, private_key = orchestrator._get_authority_credentials(uuid)
    
    # Authorize NAAN
    receipt = orchestrator.authority_manager.authorize_naan(
        wallet_address, private_key, request.naan
    )
    
    if receipt.get("already_authorized"):
        return OperationResponse(
            status="success",
            message=f"NAAN {request.naan} was already authorized for {uuid}",
            transaction_hash=None,
        )
    
    return OperationResponse(
        status="success",
        message=f"NAAN {request.naan} authorized for {uuid}",
        transaction_hash=receipt.get("transactionHash", b"").hex() if receipt.get("transactionHash") else None,
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
    orchestrator: DARKOrchestrator = Depends(get_orchestrator),
) -> OperationResponse:
    """
    Revoke a NAAN from an authority.
    
    Note: This requires the revoke_naan function to be implemented in the orchestrator.
    """
    logger.info(f"Revoking NAAN {request.naan} from authority {uuid}")
    
    # Check if authority exists
    authority = orchestrator.get_authority_by_uuid(uuid)
    
    # Check if NAAN is currently authorized
    if request.naan not in authority.naans:
        return OperationResponse(
            status="success",
            message=f"NAAN {request.naan} was not authorized for {uuid}",
            transaction_hash=None,
        )
    
    # TODO: Implement revoke_naan in orchestrator
    # For now, return a not implemented response
    raise HTTPException(
        status_code=501,
        detail="NAAN revocation not yet implemented in orchestrator"
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
    orchestrator: DARKOrchestrator = Depends(get_orchestrator),
) -> OperationResponse:
    """
    Deactivate an authority.
    
    Note: This requires the deactivate_authority function to be implemented in the orchestrator.
    """
    logger.info(f"Deactivating authority: {uuid}")
    
    # Check if authority exists
    authority = orchestrator.get_authority_by_uuid(uuid)
    
    if not authority.active:
        return OperationResponse(
            status="success",
            message=f"Authority {uuid} is already inactive",
            transaction_hash=None,
        )
    
    # TODO: Implement deactivate_authority in orchestrator
    # For now, return a not implemented response
    raise HTTPException(
        status_code=501,
        detail="Authority deactivation not yet implemented in orchestrator"
    )


# =============================================================================
# Wallet Operations
# =============================================================================

@router.get(
    "/authority/{uuid}/balance",
    response_model=BalanceResponse,
    summary="Get wallet balance",
    description="Get the wallet balance for an authority.",
)
async def get_balance(
    uuid: str = Path(..., description="Authority UUID"),
    cert_info: dict = Depends(require_mtls),
    orchestrator: DARKOrchestrator = Depends(get_orchestrator),
) -> BalanceResponse:
    """
    Get wallet balance for an authority.
    """
    logger.info(f"Getting balance for authority: {uuid}")
    
    authority = orchestrator.get_authority_by_uuid(uuid)
    balance = orchestrator.get_wallet_balance(uuid)
    
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
    orchestrator: DARKOrchestrator = Depends(get_orchestrator),
) -> OperationResponse:
    """
    Fund an authority's wallet.
    """
    logger.info(f"Funding authority {uuid} with {request.amount_eth} ETH")
    
    # Get authority to verify it exists and get wallet address
    authority = orchestrator.get_authority_by_uuid(uuid)
    
    # Convert ETH to wei
    amount_wei = orchestrator.w3.to_wei(request.amount_eth, "ether")
    
    # Fund wallet
    receipt = orchestrator._fund_wallet(authority.wallet_address, amount_wei)
    
    return OperationResponse(
        status="success",
        message=f"Funded {uuid} with {request.amount_eth} ETH",
        transaction_hash=receipt.get("transactionHash", b"").hex() if receipt.get("transactionHash") else None,
    )


# =============================================================================
# System Status
# =============================================================================

@router.get(
    "/status",
    response_model=AdminStatusResponse,
    summary="Get admin status",
    description="Get system status including admin account info and blockchain connection.",
)
async def get_status(
    cert_info: dict = Depends(require_mtls),
    orchestrator: DARKOrchestrator = Depends(get_orchestrator),
) -> AdminStatusResponse:
    """
    Get admin status and system information.
    """
    logger.info("Getting admin status")
    
    return AdminStatusResponse(
        admin_address=orchestrator.admin_account.address,
        admin_balance_eth=orchestrator.get_admin_balance(),
        blockchain_connected=orchestrator.is_connected(),
        current_block=orchestrator.get_block_number(),
        chain_id=orchestrator.config.chain_id,
    )
