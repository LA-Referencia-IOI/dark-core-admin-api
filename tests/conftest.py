"""
Pytest fixtures for dARK Core Admin API tests.
"""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

from fastapi.testclient import TestClient


@dataclass
class MockAuthorityInfo:
    """Mock authority info for testing."""
    uuid: str
    wallet_address: str
    naans: list
    active: bool


@dataclass
class MockTxReceipt:
    """Mock transaction receipt for testing."""

    tx_hash: str
    status: int = 1
    gas_used: int | None = None
    block_number: int | None = None


@pytest.fixture
def mock_authority_info():
    """Create a mock AuthorityInfo."""
    return MockAuthorityInfo(
        uuid="test-authority-123",
        wallet_address="0x1234567890abcdef1234567890abcdef12345678",
        naans=["12345", "67890"],
        active=True,
    )


@pytest.fixture
def mock_corelib_client(mock_authority_info):
    """Create a mock DARKCoreClient."""
    mock = MagicMock()

    mock.is_connected.return_value = True
    mock.get_block_number.return_value = 12345
    mock.get_admin_balance.return_value = 10.5

    mock.setup_authority.return_value = mock_authority_info
    mock.get_authority_by_uuid.return_value = mock_authority_info
    mock.get_wallet_balance.return_value = 0.01
    mock.authorize_naan.return_value = MockTxReceipt(
        tx_hash="12345678",
    )
    mock.revoke_naan.return_value = MockTxReceipt(
        tx_hash="87654321",
    )
    mock.deactivate_authority.return_value = MockTxReceipt(
        tx_hash="deadbeef",
    )
    mock.fund_authority_wallet.return_value = MockTxReceipt(
        tx_hash="abcdef12",
    )

    mock.admin_account.address = "0xadmin1234567890abcdef1234567890abcdef1234"
    mock.config.chain_id = 1337

    mock.w3.to_wei.return_value = 10000000000000000  # 0.01 ETH in wei

    return mock


@pytest.fixture
def client(mock_corelib_client):
    """Create test client with mocked dark-core-lib client."""
    from app.main import app
    from app.dependencies import get_corelib_client

    app.dependency_overrides[get_corelib_client] = lambda: mock_corelib_client

    with patch("app.main.init_corelib_client", return_value=mock_corelib_client), patch(
        "app.main.get_corelib_client", return_value=mock_corelib_client
    ):
        with TestClient(app) as test_client:
            yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth(mock_corelib_client):
    """Create test client with mTLS disabled."""
    from app.main import app
    from app.dependencies import get_corelib_client
    from app.middleware.auth import require_mtls

    app.dependency_overrides[get_corelib_client] = lambda: mock_corelib_client
    app.dependency_overrides[require_mtls] = lambda: None

    with patch("app.main.init_corelib_client", return_value=mock_corelib_client), patch(
        "app.main.get_corelib_client", return_value=mock_corelib_client
    ):
        with TestClient(app) as test_client:
            yield test_client

    app.dependency_overrides.clear()
