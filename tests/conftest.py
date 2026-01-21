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
def mock_orchestrator(mock_authority_info):
    """Create a mock DARKOrchestrator."""
    mock = MagicMock()
    
    # Mock connection methods
    mock.is_connected.return_value = True
    mock.get_block_number.return_value = 12345
    mock.get_admin_balance.return_value = 10.5
    
    # Mock authority methods
    mock.setup_authority.return_value = mock_authority_info
    mock.get_authority_by_uuid.return_value = mock_authority_info
    mock.get_wallet_balance.return_value = 0.01
    mock._get_authority_credentials.return_value = (
        mock_authority_info.wallet_address,
        "0xprivatekey123",
    )
    
    # Mock admin account
    mock.admin_account.address = "0xadmin1234567890abcdef1234567890abcdef1234"
    
    # Mock config
    mock.config.chain_id = 1337
    
    # Mock Web3 instance
    mock.w3.to_wei.return_value = 10000000000000000  # 0.01 ETH in wei
    
    # Mock authority_manager
    mock.authority_manager.authorize_naan.return_value = {
        "transactionHash": b"\x12\x34\x56\x78",
    }
    
    return mock


@pytest.fixture
def client(mock_orchestrator):
    """Create test client with mocked orchestrator."""
    from app.main import app
    from app.dependencies import get_orchestrator
    
    # Override the get_orchestrator dependency
    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    
    with patch("app.main.init_orchestrator", return_value=mock_orchestrator):
        with TestClient(app) as test_client:
            yield test_client
    
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth(mock_orchestrator):
    """Create test client with mTLS disabled."""
    from app.main import app
    from app.dependencies import get_orchestrator
    from app.middleware.auth import require_mtls
    
    # Override dependencies
    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[require_mtls] = lambda: None
    
    with patch("app.main.init_orchestrator", return_value=mock_orchestrator):
        with TestClient(app) as test_client:
            yield test_client
    
    app.dependency_overrides.clear()
