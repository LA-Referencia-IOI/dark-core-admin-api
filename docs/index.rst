dARK Core Admin API Documentation
==================================

This documentation covers the dARK Core Admin API, a REST service for
managing authorities in the dARK network through ``dark-core-lib``.

Contents
--------

.. toctree::
   :maxdepth: 2

   api

Overview
--------

The Admin API provides endpoints for:

- **Authority Management**: Register new authorities, authorize or revoke NAANs, deactivate authorities
- **Wallet Operations**: Fund authority wallets, check balances
- **System Status**: Monitor admin account and blockchain connection

Quick Start
-----------

Install dependencies::

    pip install -r requirements.txt
    pip install -e ../dark-core-lib

Configure environment::

    cp .env.example .env
    # Edit .env with your configuration

Run the server::

    uvicorn app.main:app --port 8000

For deployment, use the dark-deployer operator inventory and guided operations.
This repository does not provide a standalone Compose file.

Access documentation at http://localhost:8000/docs

Additional developer-facing docs:

- See ``README.md`` for deployment and configuration.
- See ``architecture.md`` for implementation details.
