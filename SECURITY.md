# Security Policy

UNLOOP handles OAuth credentials and listening-history data. Treat both as sensitive.

- Never commit secrets or tokens.
- Store credentials in environment variables or a platform secret store.
- Bind local development services to loopback by default.
- Request the minimum OAuth scopes necessary.
- Do not log access tokens, refresh tokens, or raw authorization headers.

For security reports, please use GitHub private vulnerability reporting once the repository is published.
