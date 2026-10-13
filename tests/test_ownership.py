"""Administrative ownership checks use chain state exclusively."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from dark_core_lib.exceptions import AuthorityNotFoundError, ARKNotFoundError
from app.services import ownership


def setup_transfer():
    core = Mock()
    source = SimpleNamespace(uuid="source", wallet_address="0xaaa", active=True)
    target = SimpleNamespace(uuid="target", wallet_address="0xbbb", active=True)
    core.get_authority_by_uuid.side_effect = lambda uuid: source if uuid == "source" else target
    core.is_authorized_for_naan.return_value = True
    request = SimpleNamespace(ark="ark:12345/test", source_authority_id="source", target_authority_id="target", reason="review")
    return core, target, request


def test_transfer_and_identical_retry_reconcile_chain():
    core, target, request = setup_transfer()
    core.get_ark.side_effect = [SimpleNamespace(owner="0xaaa"), SimpleNamespace(owner="0xbbb"), SimpleNamespace(owner="0xbbb")]
    core.transfer_ark_owner.return_value = SimpleNamespace(tx_hash="0x123")
    assert ownership.transfer(core, request)["transaction_hash"] == "0x123"
    assert ownership.transfer(core, request)["already_at_destination"]
    core.transfer_ark_owner.assert_called_once_with(request.ark, "source", "target")


@pytest.mark.parametrize("owner,active,allowed,code", [("0xccc", True, True, "CHAIN_OWNER_CHANGED"), ("0xaaa", False, True, "DESTINATION_INACTIVE_OR_UNAUTHORIZED"), ("0xaaa", True, False, "DESTINATION_INACTIVE_OR_UNAUTHORIZED")])
def test_transfer_rejects_invalid_chain_state(owner, active, allowed, code):
    core, target, request = setup_transfer()
    target.active = active
    core.is_authorized_for_naan.return_value = allowed
    core.get_ark.return_value = SimpleNamespace(owner=owner)
    with pytest.raises(HTTPException) as exc:
        ownership.transfer(core, request)
    assert exc.value.detail == code
    core.transfer_ark_owner.assert_not_called()


def test_deactivation_requires_zero_owned_pids():
    core = Mock()
    core.get_owned_ark_count.return_value = 1
    with pytest.raises(HTTPException) as exc:
        ownership.deactivate(core, "source")
    assert exc.value.status_code == 409
    core.deactivate_authority.assert_not_called()
    core.get_owned_ark_count.return_value = 0
    core.get_authority_by_uuid.return_value = SimpleNamespace(active=True)
    ownership.deactivate(core, "source")
    core.deactivate_authority.assert_called_once_with("source")


@pytest.mark.parametrize("error,detail", [(AuthorityNotFoundError("missing"), "AUTHORITY_NOT_FOUND"), (ARKNotFoundError("missing"), "ARK_NOT_FOUND"), (TimeoutError(), "TRANSFER_NOT_CONFIRMED_CHECK_CHAIN_AND_RETRY")])
def test_transfer_api_distinguishes_missing_records_from_uncertain_outcome(client_no_auth, mock_corelib_client, error, detail):
    mock_corelib_client.get_authority_by_uuid.side_effect = error
    response = client_no_auth.post("/api/v1/admin/arks/transfer-owner", json=dict(ark="ark:12345/test", source_authority_id="source", target_authority_id="target", reason="review"))
    assert response.status_code == (503 if isinstance(error, TimeoutError) else 404)
    assert response.json()["detail"] == detail
