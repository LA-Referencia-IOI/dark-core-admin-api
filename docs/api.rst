API Reference
=============

This section documents all API endpoints available in the dARK Core Admin API.

Health Check
------------

.. http:get:: /health

   Check API health status.

   **Response**:

   .. code-block:: json

      {
        "status": "healthy",
        "blockchain_connected": true,
        "current_block": 12345,
        "admin_balance_eth": 10.5
      }

Admin Status
------------

.. http:get:: /api/v1/admin/status

   Get admin account and system status.

   **Response**:

   .. code-block:: json

      {
        "admin_address": "0x...",
        "admin_balance_eth": 10.5,
        "blockchain_connected": true,
        "current_block": 12345,
        "chain_id": 1337
      }

Authority Management
--------------------

Register Authority
^^^^^^^^^^^^^^^^^^

.. http:post:: /api/v1/admin/authority

   Register a new authority with wallet and NAAN authorization.

   **Request Body**:

   .. code-block:: json

      {
        "uuid": "org-uuid-12345",
        "naans": ["12345", "67890"],
        "fund_amount_eth": 0.01
      }

   **Response**:

   .. code-block:: json

      {
        "uuid": "org-uuid-12345",
        "wallet_address": "0x...",
        "naans": ["12345", "67890"],
        "active": true,
        "balance_eth": 0.01
      }

Get Authority
^^^^^^^^^^^^^

.. http:get:: /api/v1/admin/authority/{uuid}

   Get information about a registered authority.

   **Parameters**:
   
   - ``uuid`` (path): Authority UUID

   **Response**:

   .. code-block:: json

      {
        "uuid": "org-uuid-12345",
        "wallet_address": "0x...",
        "naans": ["12345", "67890"],
        "active": true,
        "balance_eth": 0.01
      }

Authorize NAAN
^^^^^^^^^^^^^^

.. http:post:: /api/v1/admin/authority/{uuid}/authorize-naan

   Authorize an additional NAAN for an authority.

   **Parameters**:
   
   - ``uuid`` (path): Authority UUID

   **Request Body**:

   .. code-block:: json

      {
        "naan": "99999"
      }

   **Response**:

   .. code-block:: json

      {
        "status": "success",
        "message": "NAAN 99999 authorized for org-uuid-12345",
        "transaction_hash": "0x..."
      }

Wallet Operations
-----------------

Get Balance
^^^^^^^^^^^

.. http:get:: /api/v1/admin/authority/{uuid}/balance

   Get wallet balance for an authority.

   **Parameters**:
   
   - ``uuid`` (path): Authority UUID

   **Response**:

   .. code-block:: json

      {
        "uuid": "org-uuid-12345",
        "wallet_address": "0x...",
        "balance_eth": 0.015
      }

Fund Wallet
^^^^^^^^^^^

.. http:post:: /api/v1/admin/authority/{uuid}/fund

   Send ETH to an authority's wallet.

   **Parameters**:
   
   - ``uuid`` (path): Authority UUID

   **Request Body**:

   .. code-block:: json

      {
        "amount_eth": 0.01
      }

   **Response**:

   .. code-block:: json

      {
        "status": "success",
        "message": "Funded org-uuid-12345 with 0.01 ETH",
        "transaction_hash": "0x..."
      }

Error Responses
---------------

All error responses follow this format:

.. code-block:: json

   {
     "error": "ERROR_CODE",
     "message": "Human-readable message",
     "retryable": false,
     "details": null
   }

Common error codes:

- ``AUTHORITY_NOT_FOUND`` (404): Authority with given UUID not found
- ``AUTHORITY_ALREADY_EXISTS`` (409): Authority with UUID already registered
- ``AUTHORIZATION_FAILED`` (403): Not authorized for operation
- ``BLOCKCHAIN_ERROR`` (503): Blockchain transaction failed (retryable)
- ``CONFIGURATION_ERROR`` (500): Internal configuration error
