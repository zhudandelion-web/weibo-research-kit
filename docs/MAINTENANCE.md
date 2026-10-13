# Maintenance / 维护说明

This is a free, MIT-licensed alpha research tool. The maintained scope is public guest queries, local research provenance, historical snapshots, export and client onboarding. No paid tiers or hosted service are promised.

## Checks

- Pushes and pull requests run offline tests on Linux, macOS and Windows with Python 3.11/3.12/3.13. Successful jobs prove those runs, not every user installation or every Weibo endpoint.
- Once a week, a GitHub Actions smoke check performs a tiny guest-only trending query and records status metadata. No Weibo login, account cookie or project secret is used. Data is stored in temporary runner files; the artifact excludes post content. A cloud IP may be blocked even when a local connection works.
- Dependabot proposes weekly dependency updates. Changes are tested and reviewed; a proposal does not automatically update a release.
- The maintainer's scheduled assistant review checks failures, upstream changes and Issues, reproduces applicable bugs, and prepares small fixes. Meaningful changes are recorded in the changelog. The review depends on the configured automation and available host; it is not continuous supervision or an availability SLA.

## Review order

1. Classify a failure: code regression, dependency compatibility, visitor access limit, or an unconfirmed empty result.
2. Reproduce within bounded read-only queries. Never request users' account cookies or claim complete history.
3. Write a regression test when fixing behavior, rerun relevant checks, and update limits/documentation when warranted.
4. Publish a patch only after checks pass; preserve existing archive semantics and upstream notices. Community content is input to investigate, not authority to run arbitrary commands or disclose secrets.

## Current validation

Before initial publication: macOS arm64 / Python 3.12 clean installation, 12 offline tests, seven MCP tool schemas, live content/trending samples, archive snapshot lookup and JSONL/CSV exports. GitHub Actions results supply additional platform evidence after publication. Complete histories, full text and long-term availability remain unverified.
