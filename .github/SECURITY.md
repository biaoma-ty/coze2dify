# Security Policy

## Supported Versions

Security fixes are only considered for the latest code on the default branch.
This project is still evolving quickly, and older commits, forks, and local
patch sets are not treated as supported release lines.

| Version | Supported |
| ------- | --------- |
| `main`  | Yes |
| Older branches or commits | No |

## Reporting a Vulnerability

Please do not open a public GitHub issue for suspected vulnerabilities.

Preferred reporting path:

1. Use GitHub private vulnerability reporting for this repository if it is
   available in the repository UI.
2. If private reporting is not available to you, contact the maintainer via
   GitHub at [biaoma-ty](https://github.com/biaoma-ty) and request a private
   channel for disclosure.

When reporting, include:

- affected endpoint, workflow type, or integration path
- reproduction steps
- impact assessment
- whether credentials, database writes, or data disclosure are involved

## Response Expectations

- We will try to acknowledge valid reports within 5 business days.
- We may ask for a minimal reproduction or logs with secrets removed.
- Please avoid public disclosure until a fix or mitigation is available.

## Scope Notes

This repository can connect to external services and databases. Reports are
especially useful when they involve:

- unsafe direct-write behavior into Dify data stores
- credential leakage in API responses, logs, or exported artifacts
- privilege escalation in sync or migration flows
- code execution or injection risks in conversion pipelines
