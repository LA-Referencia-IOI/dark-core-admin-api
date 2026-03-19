"""
Tests for Admin API endpoints.
"""

from dark_core_lib.exceptions import AuthorityAlreadyExistsError, AuthorityNotFoundError


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check_healthy(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["blockchain_connected"] is True
        assert "current_block" in data
        assert "admin_balance_eth" in data


class TestRegisterAuthority:
    """Tests for POST /api/v1/admin/authority."""
    
    def test_register_authority_success(self, client, mock_corelib_client, mock_authority_info):
        """Test successful authority registration."""
        payload = {
            "uuid": "test-authority-123",
            "naans": ["12345", "67890"],
            "fund_amount_eth": 0.01,
        }
        
        response = client.post("/api/v1/admin/authority", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == mock_authority_info.uuid
        assert data["wallet_address"] == mock_authority_info.wallet_address
        assert data["naans"] == mock_authority_info.naans
        assert data["active"] is True
        
        mock_corelib_client.setup_authority.assert_called_once()
    
    def test_register_authority_already_exists(self, client, mock_corelib_client):
        """Test registering duplicate authority returns 409."""
        mock_corelib_client.setup_authority.side_effect = AuthorityAlreadyExistsError(
            "Authority with UUID 'test' already exists on blockchain"
        )
        
        payload = {
            "uuid": "test",
            "naans": ["12345"],
        }
        
        response = client.post("/api/v1/admin/authority", json=payload)
        
        assert response.status_code == 409
        data = response.json()
        assert data["error"] == "AUTHORITY_ALREADY_EXISTS"
    
    def test_register_authority_missing_fields(self, client):
        """Test missing required fields returns 422."""
        payload = {
            "uuid": "test-authority",
            # missing naans
        }
        
        response = client.post("/api/v1/admin/authority", json=payload)
        
        assert response.status_code == 422


class TestGetAuthority:
    """Tests for GET /api/v1/admin/authority/{uuid}."""
    
    def test_get_authority_success(self, client, mock_authority_info):
        """Test getting authority information."""
        response = client.get(f"/api/v1/admin/authority/{mock_authority_info.uuid}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == mock_authority_info.uuid
        assert data["wallet_address"] == mock_authority_info.wallet_address
        assert "balance_eth" in data
    
    def test_get_authority_not_found(self, client, mock_corelib_client):
        """Test getting non-existent authority returns 404."""
        mock_corelib_client.get_authority_by_uuid.side_effect = AuthorityNotFoundError(
            "Authority not found: unknown-uuid"
        )
        
        response = client.get("/api/v1/admin/authority/unknown-uuid")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "AUTHORITY_NOT_FOUND"


class TestAuthorizeNAAN:
    """Tests for POST /api/v1/admin/authority/{uuid}/authorize-naan."""
    
    def test_authorize_naan_success(self, client, mock_authority_info):
        """Test authorizing a new NAAN."""
        payload = {"naan": "99999"}
        
        response = client.post(
            f"/api/v1/admin/authority/{mock_authority_info.uuid}/authorize-naan",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_authorize_naan_already_authorized(self, client, mock_corelib_client, mock_authority_info):
        """Test authorizing already authorized NAAN."""
        mock_corelib_client.get_authority_by_uuid.return_value = mock_authority_info
        
        payload = {"naan": "12345"}
        
        response = client.post(
            f"/api/v1/admin/authority/{mock_authority_info.uuid}/authorize-naan",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "already authorized" in data["message"]


class TestRevokeNAAN:
    """Tests for POST /api/v1/admin/authority/{uuid}/revoke-naan."""

    def test_revoke_naan_success(self, client, mock_authority_info):
        """Test revoking an authorized NAAN."""
        payload = {"naan": "12345"}

        response = client.post(
            f"/api/v1/admin/authority/{mock_authority_info.uuid}/revoke-naan",
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "revoked" in data["message"]
        assert data["transaction_hash"] == "87654321"

    def test_revoke_naan_not_authorized(self, client, mock_corelib_client, mock_authority_info):
        """Test revoking a NAAN that is not currently authorized."""
        mock_corelib_client.get_authority_by_uuid.return_value = mock_authority_info
        payload = {"naan": "99999"}

        response = client.post(
            f"/api/v1/admin/authority/{mock_authority_info.uuid}/revoke-naan",
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "was not authorized" in data["message"]
        assert data["transaction_hash"] is None


class TestDeactivateAuthority:
    """Tests for POST /api/v1/admin/authority/{uuid}/deactivate."""

    def test_deactivate_authority_success(self, client, mock_authority_info):
        """Test deactivating an active authority."""
        response = client.post(
            f"/api/v1/admin/authority/{mock_authority_info.uuid}/deactivate"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "deactivated" in data["message"]
        assert data["transaction_hash"] == "deadbeef"

    def test_deactivate_authority_already_inactive(self, client, mock_corelib_client, mock_authority_info):
        """Test deactivating an already inactive authority."""
        mock_authority_info.active = False
        mock_corelib_client.get_authority_by_uuid.return_value = mock_authority_info

        response = client.post(
            f"/api/v1/admin/authority/{mock_authority_info.uuid}/deactivate"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "already inactive" in data["message"]
        assert data["transaction_hash"] is None


class TestFundWallet:
    """Tests for POST /api/v1/admin/authority/{uuid}/fund."""
    
    def test_fund_wallet_success(self, client, mock_corelib_client, mock_authority_info):
        """Test funding authority wallet."""
        payload = {"amount_eth": 0.05}
        
        response = client.post(
            f"/api/v1/admin/authority/{mock_authority_info.uuid}/fund",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "0.05" in data["message"]
        assert data["transaction_hash"] == "abcdef12"
    
    def test_fund_wallet_invalid_amount(self, client, mock_authority_info):
        """Test funding with invalid amount returns 422."""
        payload = {"amount_eth": -1.0}
        
        response = client.post(
            f"/api/v1/admin/authority/{mock_authority_info.uuid}/fund",
            json=payload
        )
        
        assert response.status_code == 422


class TestGetBalance:
    """Tests for GET /api/v1/admin/authority/{uuid}/balance."""
    
    def test_get_balance_success(self, client, mock_authority_info):
        """Test getting wallet balance."""
        response = client.get(f"/api/v1/admin/authority/{mock_authority_info.uuid}/balance")
        
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == mock_authority_info.uuid
        assert "balance_eth" in data
        assert "wallet_address" in data


class TestAdminStatus:
    """Tests for GET /api/v1/admin/status."""
    
    def test_admin_status_success(self, client):
        """Test getting admin status."""
        response = client.get("/api/v1/admin/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "admin_address" in data
        assert "admin_balance_eth" in data
        assert "blockchain_connected" in data
        assert "current_block" in data
        assert "chain_id" in data
