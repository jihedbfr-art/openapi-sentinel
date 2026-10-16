# Conventions behind the checks

[Version française](conventions.fr.md)

The rules in `openapi-sentinel` come from reading five public Open API descriptions, fixed to exact commits so anyone can repeat the observation. Read on 2026-10-16. These are habits seen in those files, not an official rule set, and nothing here reproduces a schema or an example payload.

## The five files

| API | File (pinned commit) | Licence of the repository |
|---|---|---|
| Product Catalog Management 4.1.0 | [TMF620](https://github.com/tmforum-apis/TMF620_ProductCatalog/blob/24e69f3026f2b514baa27d7206540fc7b55bcb45/TMF620-ProductCatalog-v4.1.0.swagger.json) | Apache-2.0, [LICENSE](https://github.com/tmforum-apis/TMF620_ProductCatalog/blob/24e69f3026f2b514baa27d7206540fc7b55bcb45/LICENSE) |
| Product Ordering 4.0.0 | [TMF622](https://github.com/tmforum-apis/TMF622_ProductOrder/blob/a3825f95248eb04fb1c7e2321305bc99631168a4/TMF622-ProductOrder-v4.0.0.swagger.json) | Apache-2.0, [LICENSE](https://github.com/tmforum-apis/TMF622_ProductOrder/blob/a3825f95248eb04fb1c7e2321305bc99631168a4/LICENSE) |
| Service Inventory Management 4.0.0 | [TMF638](https://github.com/tmforum-apis/TMF638_ServiceInventory/blob/50fc82942e423c81896362d1ab9847f7c918cf7f/TMF638-ServiceInventory-v4.0.0.swagger.json) | Apache-2.0, [LICENSE](https://github.com/tmforum-apis/TMF638_ServiceInventory/blob/50fc82942e423c81896362d1ab9847f7c918cf7f/LICENSE) |
| Product Inventory 4.0.0 | [TMF637](https://github.com/tmforum-apis/TMF637_ProductInventory/blob/f598b4a02186071f2794b8f9b4f6904ef0a8aa52/TMF637-ProductInventory-v4.0.0.swagger.json) | Apache-2.0, [LICENSE](https://github.com/tmforum-apis/TMF637_ProductInventory/blob/f598b4a02186071f2794b8f9b4f6904ef0a8aa52/LICENSE) |
| Resource Inventory Management 4.0.0 | [TMF639](https://github.com/tmforum-apis/TMF639_ResourceInventory/blob/2693a854940de3c6e15b1aade24f981d94b75d3a/TMF639-ResourceInventory-v4.0.0.swagger.json) | Apache-2.0, [LICENSE](https://github.com/tmforum-apis/TMF639_ResourceInventory/blob/2693a854940de3c6e15b1aade24f981d94b75d3a/LICENSE) |

All five are Swagger 2.0 files. The licence statement applies to those repositories only. This project copies none of their content; it reads their structure.

## What was observed, and the rule it became

| Observation (all five files) | Rule |
|---|---|
| Every operation has an `operationId` | S001 |
| Every collection `GET` has `fields`, `offset` and `limit` query parameters | S002 |
| Every collection `GET` 200 declares `X-Total-Count` and `X-Result-Count` | S003 |
| Entity schemas that carry an `href` also carry `id`, and nearly all carry `@type` | S004 |
| Operations declare 400, 401, 403, 404, 405, 409 and 500 responses; this tool asks only for 400 and 500 (404 on identifier paths) | S005 |
| A `/hub` path with a registration operation, plus `/listener/...` paths for events | S006 (the listener paths are not checked) |
| `info.version` is set | S007 |

Event payload schemas (names ending in `Event`) do not follow the entity pattern in these files, so S004 skips them. Running the tool on the five files returns five S004 warnings (`Addressable` in two files, `EntityValue`, `Place`, `Service`) and nothing else: the rules are as strict as the files themselves, no stricter.

## What this does not establish

A rule that passes does not show conformance to any specification, and a rule that fails does not show an API is wrong. Newer versions of these APIs may differ. Check the official publication for what applies to your case.
