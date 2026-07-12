# TLS certificate mount point

Do not commit certificates or private keys.

For local disposable validation, place a task-created self-signed pair here:

- `fullchain.pem`
- `privkey.pem`

For a remote staging server, set `TLS_CERT_DIRECTORY` to an external absolute
directory containing those filenames. Keep the private key readable only by the
operator and Docker service account. Certificate issuance and DNS changes are
manual gates and are not performed by the deployment scripts.
