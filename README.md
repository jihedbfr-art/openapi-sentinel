<p align="center">
  <img src="assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="120" height="120">
</p>

# openapi-sentinel

[Version française](README.fr.md)

Check an OpenAPI/Swagger description against the habits of telecom-style REST APIs, and list the changes between two versions that would break existing callers. Offline, no account, no dependency, no AI required.

> Independent project. Not affiliated with, endorsed by or certified by TM Forum or any standards body. Passing these checks says nothing about conformance to any specification.

## Why it exists

Public telecom Open API descriptions share a lot of structure: the same paging parameters, the same count headers, entities that carry `id`, `href` and `@type`, a `/hub` endpoint for notifications. Teams that publish their own APIs in this style drift from it without noticing, and a renamed or removed field breaks consumers quietly. This tool turns those habits into checks you can run in a minute, and it tells you which public files the habit was observed in ([docs/conventions.md](docs/conventions.md)).

## Quick start

Python 3.10 or later. Nothing to install to try it from a clone:

```bash
git clone https://github.com/jihedbfr-art/openapi-sentinel.git
cd openapi-sentinel
PYTHONPATH=src python -m openapi_sentinel lint fixtures/offer-api-weak.json
PYTHONPATH=src python -m openapi_sentinel diff fixtures/offer-api-v1.json fixtures/offer-api-v2.json
```

Or install it (`pip install .`) and use the `openapi-sentinel` command. JSON files work out of the box; YAML needs `pip install pyyaml`.

Options: `--lang en|fr` (messages and report labels; `--help` stays in English), `--format text|json|md|sarif`, and for `lint` `--fail-on error|warn|never` (default `error`). Exit codes: `lint` returns `0` when no finding reaches the `--fail-on` level (warnings and infos may still be printed) and `1` otherwise; `diff` returns `0` when it finds no breaking change and `1` otherwise; `2` means unreadable or malformed input.

## SARIF reports

Use `--format sarif` before `lint` or `diff` to write SARIF 2.1.0 JSON to stdout:

```bash
PYTHONPATH=src python -m openapi_sentinel --format sarif lint fixtures/offer-api-weak.json > results.sarif
PYTHONPATH=src python -m openapi_sentinel --lang fr --format sarif diff fixtures/offer-api-v1.json fixtures/offer-api-v2.json > changes.sarif
```

The report includes all core rule descriptions in English and one result per finding, with messages in the requested language. `error`, `warn` and `info` become `error`, `warning` and `note`; every diff result is an `error`. An empty report has an empty `results` array. Exit codes and `--fail-on` keep their existing meaning.

Locations contain an encoded file URI and the finding's logical path, without guessed line numbers. Paths inside the current working directory are relative; external files retain an absolute file URI. Run from the repository root for portable uploads. Removed paths, operations, responses and fields point to the old file; new requirements and changed types point to the new file. Keep both descriptions in the checkout for a diff upload. External rule packs receive a generic English rule description and retain their own result messages.

The following is a **copyable job fragment**, not an installed workflow. It assumes Python 3.10+ and this repository's source layout; adapt the input path to your repository. The upload still runs after findings (exit 1), while the check remains failed. Input errors (exit 2) fail the check and skip upload. For diff reports use the diff command and a separate category such as `openapi-sentinel-diff`.

```yaml
permissions:
  contents: read
  security-events: write
steps:
  - uses: actions/checkout@v6
  - name: Check API
    id: sentinel
    shell: bash
    run: |
      status=0
      PYTHONPATH=src python -m openapi_sentinel --format sarif lint fixtures/offer-api-weak.json > results.sarif || status=$?
      echo "status=$status" >> "$GITHUB_OUTPUT"
      exit "$status"
  - name: Upload SARIF
    if: ${{ !cancelled() && (steps.sentinel.outputs.status == '0' || steps.sentinel.outputs.status == '1') }}
    uses: github/codeql-action/upload-sarif@v4
    with:
      sarif_file: results.sarif
      category: openapi-sentinel-lint
```

GitHub documents the upload action and required permissions in [Uploading a SARIF file](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/integrate-with-existing-tools/upload-sarif-file) (consulted 2026-10-18). The output follows the [OASIS SARIF 2.1.0 schema](https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/schemas/sarif-schema-2.1.0.json) (consulted 2026-10-18). Local schema validation does not confirm acceptance by a hosted code scanning service; no live upload was performed for this change.

## What it checks

| Rule | Level | Checks |
|---|---|---|
| S001 | error/warn | every operation has a unique `operationId` |
| S002 | warn | collection `GET` accepts `fields`, `offset`, `limit` |
| S003 | warn | collection `GET` 200 declares `X-Total-Count` and `X-Result-Count` |
| S004 | warn | schemas with an `href` also have `id` and `@type` (notification payloads ending in `Event` are skipped) |
| S005 | warn | each operation declares 400 and 500, plus 404 on paths with an identifier |
| S006 | info | a `POST /hub` registration endpoint exists |
| S007 | warn | `info.version` is present |
| S008 | info | each operation has a summary or description |

`diff` reports: path removed (D001), operation removed (D002), new required input (D003), success response removed (D004), response field removed (D005), field type changed (D006). Additive changes are not reported.

## Limits

- Static checks on the description file only. Nothing is called, so behaviour of a running service is not tested.
- Swagger 2.0 and OpenAPI 3.x are read; only local `$ref` pointers are followed.
- The conventions are observations from five public files, summarised in [docs/conventions.md](docs/conventions.md). They are a starting point, not a standard. Run on those same five files, the tool reports five schemas (`Addressable` twice, `EntityValue`, `Place`, `Service`) that carry an `href` without an `@type`, and nothing else.
- `diff` compares top-level and nested object properties, not `oneOf`/`anyOf` variants or enum values, and a field turning optional or a narrower format are not reported. A field removed from a request body is not reported, although a strict server may reject callers that still send it.

## Tests

```bash
python -m unittest discover -s tests
```

39 tests, standard library only. Fixtures are invented APIs in `fixtures/`.

See [mutation coverage](docs/mutations.md) for the fixed seed, 3,000 inputs, 9,000 calls and limits.

## Extending

Rule functions can be added from outside through the `openapi_sentinel.rule_packs` entry-point group; see [docs/extending.md](docs/extending.md).

## Study path

The ideas behind these checks are explained, with sources and exercises, in the bilingual study path [oda-learning-lab](https://github.com/jihedbfr-art/oda-learning-lab/blob/main/docs/en/04-open-apis-in-practice.md) (Module 4).

## Licence and contact

Code: [Apache License 2.0](LICENSE). Advanced features can be discussed on request: see [COMMERCIAL.md](COMMERCIAL.md).

---

<p align="center">
  <img src="assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="80" height="80"><br>
  <sub>Built and maintained under <b>JihedAiLabs</b>.</sub>
</p>
