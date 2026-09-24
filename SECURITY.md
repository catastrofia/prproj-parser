# Security Policy

## Supported versions

Only the latest release receives security fixes.

## Reporting a vulnerability

Use GitHub private vulnerability reporting if it is enabled for this repository. If it is not enabled and no private maintainer contact is listed on GitHub, open a public issue asking for a private reporting channel without including exploit details or private `.prproj` content.

## Scope

Security-relevant reports include:

- malformed `.prproj` files that crash, hang, or exhaust CPU/memory/disk;
- unsafe XML behavior, including entity expansion or external entity handling;
- path or data leakage from parsed project contents;
- arbitrary file or network access triggered by parsing.

`.prproj` files can contain local paths, user names, client names, and other project metadata. Minimize or redact samples before sharing them.
