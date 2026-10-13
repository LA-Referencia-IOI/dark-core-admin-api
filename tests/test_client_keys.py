import base64
from unittest.mock import Mock


def test_register_with_client_key(client_no_auth, mock_corelib_client):
    public = bytes([7])*32
    response = client_no_auth.post('/api/v1/admin/authority',json={
        'uuid':'test-uuid','naans':['12345'],'client_public_key':base64.b64encode(public).decode()})
    assert response.status_code == 200
    assert mock_corelib_client.setup_authority.call_args.kwargs['client_public_key'] == public


def test_invalid_key_has_no_side_effect(client_no_auth,mock_corelib_client):
    response = client_no_auth.post('/api/v1/admin/authority',json={'uuid':'test-uuid','naans':['12345'],'client_public_key':'bad'})
    assert response.status_code == 422
    mock_corelib_client.setup_authority.assert_not_called()


def test_replace_key(client_no_auth,mock_corelib_client):
    public=bytes([9])*32
    mock_corelib_client.set_authority_client_key.return_value=Mock(tx_hash='confirmed')
    response=client_no_auth.put('/api/v1/admin/authority/test-uuid/client-key',json={'client_public_key':base64.b64encode(public).decode()})
    assert response.status_code == 200
    mock_corelib_client.set_authority_client_key.assert_called_once_with('test-uuid',public)


def test_read_current_key_from_chain(client_no_auth,mock_corelib_client):
    import hashlib
    key=bytes([7])*32
    mock_corelib_client.get_authority_auth.return_value=(key,True)
    response=client_no_auth.get('/api/v1/admin/authority/test-uuid/client-key')
    assert response.status_code==200
    assert response.json()=={'uuid':'test-uuid','client_public_key':base64.b64encode(key).decode(),'key_id':hashlib.sha256(key).hexdigest(),'active':True}


def test_read_missing_key_is_distinct_from_failure(client_no_auth,mock_corelib_client):
    mock_corelib_client.get_authority_auth.return_value=(bytes(32),True)
    response=client_no_auth.get('/api/v1/admin/authority/test-uuid/client-key')
    assert response.status_code==200
    assert response.json()['client_public_key'] is None
    assert response.json()['key_id'] is None
    from dark_core_lib.exceptions import AuthorityError
    mock_corelib_client.get_authority_auth.side_effect=AuthorityError('RPC unavailable')
    response=client_no_auth.get('/api/v1/admin/authority/test-uuid/client-key')
    assert response.status_code==400


def test_register_openssh_public_key(client_no_auth,mock_corelib_client):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    public=Ed25519PrivateKey.generate().public_key()
    ssh=public.public_bytes(serialization.Encoding.OpenSSH,serialization.PublicFormat.OpenSSH).decode()+' client-label'
    raw=public.public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    response=client_no_auth.post('/api/v1/admin/authority',json={'uuid':'test-uuid','naans':['12345'],'client_public_key':ssh})
    assert response.status_code==200
    assert mock_corelib_client.setup_authority.call_args.kwargs['client_public_key']==raw
