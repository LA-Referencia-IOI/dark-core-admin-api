"""
Request models for dARK Core Admin API.

Pydantic models for API requests.
"""

from typing import Optional
from pydantic import BaseModel, Field


class RegisterAuthorityRequest(BaseModel):
    """Request to register a new authority."""
    
    uuid: str = Field(
        ...,
        description="Unique identifier for the authority (from external system)",
        examples=["org-uuid-12345"],
    )
    naans: list[str] = Field(
        ...,
        description="List of NAANs to authorize for this authority",
        examples=[["12345", "67890"]],
    )
    fund_amount_eth: Optional[float] = Field(
        None,
        description="Amount of ETH to fund the wallet (uses default if not specified)",
        ge=0.0,
        examples=[0.01],
    )


class AuthorizeNAANRequest(BaseModel):
    """Request to authorize an additional NAAN for an authority."""
    
    naan: str = Field(
        ...,
        description="NAAN to authorize",
        examples=["12345"],
    )


class RevokeNAANRequest(BaseModel):
    """Request to revoke a NAAN from an authority."""
    
    naan: str = Field(
        ...,
        description="NAAN to revoke",
        examples=["12345"],
    )


class FundWalletRequest(BaseModel):
    """Request to fund an authority's wallet."""
    
    amount_eth: float = Field(
        ...,
        description="Amount of ETH to send",
        gt=0.0,
        examples=[0.01],
    )
