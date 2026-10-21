# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Add entries under [Unreleased], creating only the subsections you need:
Added, Changed, Deprecated, Removed, Fixed, Security.
On release, rename [Unreleased] to [X.Y.Z] - YYYY-MM-DD, tag vX.Y.Z and
add compare links at the bottom.
-->

## [Unreleased]

### Added

- ADR-0002 adopting the Standard Webhooks v1.0.0 specification (HMAC-SHA256
  `v1` scheme) for signing deliveries, covering spoofing, tampering, replay,
  duplicate deliveries and zero-downtime secret rotation.
- Functional and non-functional requirements document with stable IDs that
  ADRs, issues and tests can reference.

### Changed

- Architecture diagram now separates the public tenant Management API from the
  internal platform Operator API, reflecting their different audiences,
  permissions and exposure.

## [0.1.0] - 2026-10-20

### Added

- Initial project scaffold with the package layout for the API, database,
  dispatcher, domain, observability and security modules.
- Architecture overview diagram in the README.
- ADR-0001 documenting the choice of Postgres over Redis Streams and Kafka as
  the queue.

[Unreleased]: https://github.com/dandobjim/pg-webhook-gateway/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dandobjim/pg-webhook-gateway/releases/tag/v0.1.0
