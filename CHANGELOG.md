# Changelog

## Unreleased

- Composite GitHub Action for lint/diff and SARIF reports, with an isolated Python environment and workspace path checks.
- Runner tests and Ubuntu/Windows integration workflow; EN/FR guide with commit-pinned examples.

[Version française](CHANGELOG.fr.md)

## 0.2.1

Added a deterministic robustness check: 3,000 fixture mutations and 9,000 CLI calls across lint, diff in both directions, all four output formats and both languages. It covers key deletion, value replacement, list duplication, object clearing and JSON truncation, and requires readable errors without tracebacks. No unhandled exception was found in this corpus. See [mutation coverage](docs/mutations.md).

Reuse the CLI parser and per-report file URIs; emit SARIF without indentation while preserving its JSON structure.

## 0.2.0

Added SARIF 2.1.0 output for lint and diff, with translated result messages, English rule descriptions, file URIs and logical locations. Exit codes are unchanged. Both READMEs include a copyable upload example. 38 tests.

## 0.1.2

Fixes found by an independent review, each reproduced first: `diff` now compares scalar and array-element types, root response types, dictionary values (`additionalProperties`), every media type, OpenAPI 3 parameter schemas, `trace` operations, a request body turning required, and nested fields turning required; `allOf` branch order no longer changes which fields are required; count header names are matched case-insensitively (S003); malformed `parameters`/`responses` give a readable error (exit 2) instead of a traceback; `--lang fr` also translates report labels. 28 tests.

## 0.1.1

Fix: `diff` now compares nested object properties and the elements of array responses (0.1.0 only looked at top-level fields of single objects and missed changes inside collections). New required inputs are reported only for top-level body fields. 20 tests.

## 0.1.0

First public version: eight convention checks (`lint`), six breaking-change checks (`diff`), English and French messages, text/JSON/Markdown output, rule-pack entry point, 18 tests.
