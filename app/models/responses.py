"""
Response models for dARK Core Admin API.

Pydantic models for API responses.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# =============================================================================
# Authority Responses
# =============================================================================

class AuthorityResponse(BaseModel):
    """Authority information response."""
    
    uuid: str = Field(..., description="Authority UUID")
    wallet_address: str = Field(..., description="Ethereum wallet address")
    naans: list[str] = Field(
        ...,
        description="List of authorized NAANs"
    )
    active: bool = Field(..., description="Whether the authority is active")
    balance_eth: Optional[float] = Field(
        None,
        description="Wallet balance in ETH"
    )


class BalanceResponse(BaseModel):
    """Wallet balance response."""
    
    uuid: str = Field(..., description="Authority UUID")
    wallet_address: str = Field(..., description="Ethereum wallet address")
    balance_eth: Optional[float] = Field(..., description="Balance in ETH")


# =============================================================================
# Operation Responses
# =============================================================================

class OperationResponse(BaseModel):
    """Response for administrative operations."""
    
    status: Literal["success", "error"] = Field(
        ...,
        description="Operation status"
    )
    message: str = Field(..., description="Human-readable message")
    transaction_hash: Optional[str] = Field(
        None,
        description="Blockchain transaction hash (if applicable)"
    )


# =============================================================================
# Status Responses
# =============================================================================

class AdminStatusResponse(BaseModel):
    """Admin status and system information."""
    
    admin_address: str = Field(..., description="Admin wallet address")
    admin_balance_eth: float = Field(..., description="Admin wallet balance in ETH")
    blockchain_connected: bool = Field(..., description="Whether connected to blockchain")
    current_block: int = Field(..., description="Current blockchain block number")
    chain_id: int = Field(..., description="Blockchain chain ID")


# =============================================================================
# Error Responses
# =============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str = Field(
        ...,
        description="Error code"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    retryable: bool = Field(
        False,
        description="Whether the request can be retried"
    )
    details: Optional[dict] = Field(
        None,
        description="Additional error details"
    )


# =============================================================================
# ARK Responses
# =============================================================================

class ArkCountResponse(BaseModel):
    """Total ARK count response."""
    
    count: int = Field(..., description="Total number of ARKs on blockchain")


class RecentArkItem(BaseModel):
    """Individual ARK information for recent list."""
    
    pid: str = Field(..., description="ARK PID (e.g., ark:/12345/name)")
    naan: str = Field(..., description="NAAN of the ARK")
    name: str = Field(..., description="Name of the ARK")
    owner: str = Field(..., description="Wallet address of the owner")
    url: str = Field(..., description="Target URL")
    cid: str = Field(..., description="Level-1 metadata CID")


class RecentArksResponse(BaseModel):
    """Recent ARKs list response."""
    
    limit: int = Field(..., description="Number of items requested")
    arks: list[RecentArkItem] = Field(..., description="List of recent ARKs")
