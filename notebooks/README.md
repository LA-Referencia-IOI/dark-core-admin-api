# Admin API Test Notebook

This directory currently contains one notebook for HTTP-level validation of the admin service:

- `admin_api_test.ipynb`

## Mental Model

The notebook talks to the already running Admin API over HTTP. It does not import the app internals directly.

That means:

- the Admin API must already be up before running the notebook
- the notebook is validating the deployed HTTP surface
- all authority registration and admin actions happen through real API calls

## Shared Environment Variables

The notebook reads:

- `ADMIN_API_BASE_URL` with default `http://localhost:8000`

From that base URL it derives:

- `/health`
- `/api/v1/admin/status`
- the rest of the admin endpoints

## Execution Notes

- if the service was installed from the root installer, it may already have a generated `.env.integration`
- the notebook assumes the service itself has the correct blockchain configuration already loaded
- in local development, the current middleware allows requests when `MTLS_ENABLED=false`
- in production-like setups with `MTLS_ENABLED=true`, this notebook would need to run through the proper mTLS path

## Recommended Usage

Run the notebook when you want to validate:

1. API health
2. admin status
3. authority registration
4. authority lookup
5. NAAN authorization changes
6. funding and balance operations

For service internals and architecture, see:

- [../README.md](../README.md)
- [../admin-architecture.md](../admin-architecture.md)
