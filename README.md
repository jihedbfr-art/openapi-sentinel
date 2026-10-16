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

Options: `--lang en|fr`, `--format text|json|md`, and for `lint` `--fail-on error|warn|never`. Exit codes: `0` clean, `1` findings (or breaking changes), `2` unreadable input.

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
- `diff` compares top-level and nested object properties, not `oneOf` variants or enum values. A field removed from a request body is not reported, although a strict server may reject callers that still send it.

## Tests

```bash
python -m unittest discover -s tests
```

20 tests, standard library only. Fixtures are invented APIs in `fixtures/`.

## Extending

Rule functions can be added from outside through the `openapi_sentinel.rule_packs` entry-point group; see [docs/extending.md](docs/extending.md).

## Licence and contact

Code: [Apache License 2.0](LICENSE). Advanced features can be discussed on request: see [COMMERCIAL.md](COMMERCIAL.md).

---

<p align="center">
  <img src="assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="80" height="80"><br>
  <sub>Built and maintained under <b>JihedAiLabs</b>.</sub>
</p>
