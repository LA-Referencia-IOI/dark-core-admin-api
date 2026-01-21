# dARK Core Admin API

REST API service for dARK Authority management. This API is designed to run on a dedicated **Admin Node** and provides administrative operations for managing authorities in the dARK network.

## Overview

The Admin API provides endpoints for:

- **Authority Management**: Register new authorities, authorize NAANs, deactivate authorities
- **Wallet Operations**: Fund authority wallets, check balances
- **System Status**: Monitor admin account and blockchain connection

> **Security Note**: This API provides administrative privileges over the dARK network. It should only be accessible to authorized administrators and must be protected with mTLS in production.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Admin Node                               │
│  ┌──────────────────────┐    ┌────────────────────────────┐ │
│  │  dark-core-admin-api │───▶│  dark-core-orchestrator    │ │
│  │    (Port 8001)       │    │  (Authority Management)     │ │
│  └──────────────────────┘    └────────────────────────────┘ │
└─────────────────────────────────│────────────────────────────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   Blockchain    │
                        │  Authority.sol  │
                        └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.9+
- Access to dARK blockchain network
- Admin private key with Authority contract admin role

### Setup

```bash
# Clone and navigate to directory
cd dark-core-admin-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install orchestrator library
pip install -e ../dark-core-orchestrator

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

Edit `.env` with your settings:

```env
# API Server
ADMIN_API_HOST=0.0.0.0
ADMIN_API_PORT=8001

# mTLS (enable in production)
MTLS_ENABLED=true
TLS_CERT_FILE=/path/to/server.crt
TLS_KEY_FILE=/path/to/server.key
TLS_CA_FILE=/path/to/ca.crt

# Blockchain
DARK_RPC_URL=http://localhost:8545
DARK_CHAIN_ID=1337
DARK_AUTHORITY_ADDRESS=0x...
DARK_CONTRACT_ADDRESS=0x...
DARK_ADMIN_PRIVATE_KEY=0x...

# Admin settings
DEFAULT_FUND_AMOUNT_ETH=0.01
```

## Running

### Development

```bash
uvicorn app.main:app --reload --port 8001
```

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### Docker

```bash
docker build -t dark-core-admin-api .
docker run -p 8001:8001 --env-file .env dark-core-admin-api
```

## API Endpoints

### Health Check

```
GET /health
```

### Authority Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/admin/authority` | Register new authority |
| GET | `/api/v1/admin/authority/{uuid}` | Get authority info |
| POST | `/api/v1/admin/authority/{uuid}/authorize-naan` | Authorize NAAN |
| POST | `/api/v1/admin/authority/{uuid}/revoke-naan` | Revoke NAAN |
| POST | `/api/v1/admin/authority/{uuid}/deactivate` | Deactivate authority |

### Wallet Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/authority/{uuid}/balance` | Get wallet balance |
| POST | `/api/v1/admin/authority/{uuid}/fund` | Fund wallet |

### System Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/status` | Admin status and blockchain info |

## API Documentation

Once running, access:

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Security

### mTLS Authentication

In production, enable mTLS to require client certificates:

1. Set `MTLS_ENABLED=true`
2. Configure TLS certificate paths
3. Only clients with valid certificates signed by the CA can access the API

### Network Isolation

The Admin API should run on an isolated network, accessible only to authorized administrators.

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black app/ tests/
ruff check app/ tests/
```

## License

AGPL-3.0-or-later
