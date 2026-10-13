"""
Request models for dARK Core Admin API.

Pydantic models for API requests.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator
from dark_core_lib.request_signing import public_key_bytes


class RegisterAuthorityRequest(BaseModel):
    """Request to register a new authority."""
    
    client_public_key: Optional[str] = None

    @field_validator("client_public_key")
    @classmethod
    def validate_client_key(cls, value):
        if value is not None:
            public_key_bytes(value)
        return value

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


class SetClientKeyRequest(BaseModel):
    client_public_key: str

    @field_validator("client_public_key")
    @classmethod
    def validate_key(cls, value):
        public_key_bytes(value)
        return value


class TransferARKOwnerRequest(BaseModel):
    ark: str = Field(..., min_length=1, max_length=255)
    source_authority_id: str = Field(..., min_length=1, max_length=255)
    target_authority_id: str = Field(..., min_length=1, max_length=255)
    reason: str = Field(..., min_length=1, max_length=2000)

    @field_validator("reason")
    @classmethod
    def nonempty_reason(cls, value):
        if not value.strip():
            raise ValueError("Reason is required")
        return value.strip()

    @field_validator("ark")
    @classmethod
    def canonical_ark(cls, value):
        from dark_core_lib.ark_id import parse_ark_id
        from dark_core_lib.exceptions import ARKError
        try:
            return parse_ark_id(value).compact
        except ARKError as exc:
            raise ValueError(str(exc)) from exc
