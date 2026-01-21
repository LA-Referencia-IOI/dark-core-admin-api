dARK Core Admin API Documentation
==================================

This documentation covers the dARK Core Admin API, a REST service for 
managing authorities in the dARK network.

Contents
--------

.. toctree::
   :maxdepth: 2

   api

Overview
--------

The Admin API provides endpoints for:

- **Authority Management**: Register new authorities, authorize NAANs
- **Wallet Operations**: Fund authority wallets, check balances
- **System Status**: Monitor admin account and blockchain connection

Quick Start
-----------

Install dependencies::

    pip install -r requirements.txt
    pip install -e ../dark-core-orchestrator

Configure environment::

    cp .env.example .env
    # Edit .env with your configuration

Run the server::

    uvicorn app.main:app --port 8001

Access documentation at http://localhost:8001/docs
