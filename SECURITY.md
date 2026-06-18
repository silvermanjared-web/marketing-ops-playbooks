# Security Policy

## Supported Versions

This repository contains marketing operations playbooks, frameworks, and validation scripts. It is not a deployed application, hosted service, or production API.

Security updates apply to the current `main` branch only.

| Version / Branch | Supported |
|---|---|
| `main` | :white_check_mark: |
| Archived branches, forks, or local copies | :x: |

## Scope

Security-sensitive issues may include:

- Accidentally committed secrets, credentials, API keys, tokens, or private URLs
- Example files that expose private campaign, customer, account, or business data
- Validation scripts that encourage unsafe handling of source data
- Documentation that includes sensitive internal process, client, or platform information
- Output examples that could reveal private performance, audience, or account data
- Unsafe assumptions around uploaded CSVs, local files, or exported reports

Out of scope:

- General playbook feedback
- Marketing strategy disagreements
- Non-security bugs in example scripts
- Requests for new frameworks or validation tools
- Low-signal automated reports unrelated to repository contents
- Misconfiguration in a user's local environment outside the documented setup

## Reporting a Vulnerability

Please do not open a public GitHub issue for security-sensitive concerns.

To report a vulnerability or sensitive-content exposure, contact:

**Jared Silverman**  
**Email:** silverman.jared@gmail.com

Please include:

- A short description of the concern
- The affected file, folder, script, or example if known
- Why the issue may create security, privacy, licensing, or confidentiality risk
- Any suggested remediation
- Whether the information appears to be publicly accessible

## Response Expectations

Good-faith reports will be reviewed as soon as practical.

If the report is accepted, remediation may include:

- Removing or redacting sensitive content
- Updating examples, documentation, or defaults
- Revising script guidance around local data handling
- Removing private or proprietary details
- Adding clearer public-safe usage guidance

If the report is declined, the reason will be explained when appropriate.

## Disclosure Policy

Please allow time for review and remediation before sharing any security-sensitive concern publicly.

This repository is intended to support responsible, public-safe marketing operations playbooks. Reports that help keep the project safe, accurate, and appropriately scoped are welcome.
