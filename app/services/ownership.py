"""Blockchain-only administrative ownership operations.

Each authority belongs to one Minter. Admin never reads or mutates its database.
The contract is the source of truth; retries reconcile the desired owner rather
than claiming persistence of a request or transaction in an Admin database.
"""
import logging
from threading import Lock
from fastapi import HTTPException, Request
from dark_core_lib.ark_id import parse_ark_id

logger = logging.getLogger(__name__)
_write_lock = Lock()


def fail(status, code):
    raise HTTPException(status, detail=code, headers={'X-DARK-Error-Code': code})


def serialize_admin_writes(request: Request):
    if request.method not in {'POST', 'PUT', 'DELETE', 'PATCH'}:
        yield
        return
    # Process-local nonce serialization, not a distributed lock. Operators must
    # serialize use of the common admin wallet across independent instances.
    if not _write_lock.acquire(blocking=False):
        fail(409, 'ADMIN_WALLET_BUSY')
    try:
        yield
    finally:
        _write_lock.release()


def summary(client, authority_id, page=None):
    count = client.get_owned_ark_count(authority_id)
    result = {'authority_id': authority_id, 'on_chain_count': count,
        'can_deactivate': count == 0, 'source': 'blockchain'}
    if page is not None:
        wallet = client.get_authority_by_uuid(authority_id).wallet_address
        records, total = client.arks.owned_records(wallet, (page-1)*50, 50)
        result.update(on_chain_count=total, can_deactivate=total == 0,
            page=page, page_size=50, records=records)
    return result


def deactivate(client, authority_id):
    if client.get_owned_ark_count(authority_id):
        fail(409, 'AUTHORITY_HAS_ASSOCIATED_PIDS')
    if not client.get_authority_by_uuid(authority_id).active:
        return None
    return client.deactivate_authority(authority_id)


def transfer(client, request):
    identifier = parse_ark_id(request.ark)
    if request.source_authority_id == request.target_authority_id:
        fail(422, 'SAME_SOURCE_AND_TARGET')
    source = client.get_authority_by_uuid(request.source_authority_id)
    target = client.get_authority_by_uuid(request.target_authority_id)
    if not target.active or not client.is_authorized_for_naan(target.uuid, identifier.naan):
        fail(409, 'DESTINATION_INACTIVE_OR_UNAUTHORIZED')
    chain = client.get_ark(identifier.naan, identifier.name)
    # Repeating a desired change reconciles current state. This is not a claim
    # about who sent the earlier transaction or a durable request-id history.
    if chain.owner.lower() == target.wallet_address.lower():
        return {'status': 'complete', 'ark': identifier.compact,
            'transaction_hash': None, 'already_at_destination': True}
    if chain.owner.lower() != source.wallet_address.lower():
        fail(409, 'CHAIN_OWNER_CHANGED')
    logger.info('PID ownership transfer requested ark=%s source=%s target=%s reason=%s',
        identifier.compact, source.uuid, target.uuid, request.reason)
    receipt = client.transfer_ark_owner(identifier.compact, source.uuid, target.uuid)
    current = client.get_ark(identifier.naan, identifier.name)
    if current.owner.lower() != target.wallet_address.lower():
        fail(409, 'CHAIN_OWNER_CHANGED_AFTER_TRANSFER')
    return {'status':'complete', 'ark':identifier.compact,
        'transaction_hash':receipt.tx_hash, 'already_at_destination':False,
        'source_authority_id':source.uuid, 'target_authority_id':target.uuid}
