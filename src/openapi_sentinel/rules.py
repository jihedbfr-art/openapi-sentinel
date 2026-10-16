"""Convention checks. Each rule is a function (doc) -> list of Finding.

The conventions come from reading five public telecom Open API descriptions (see
docs/conventions.md). They are habits observed in those files, not an official rule set.
"""
from dataclasses import dataclass

from .core import operations, properties, resolve, response_codes, schemas

ERROR, WARN, INFO = "error", "warn", "info"

MESSAGES = {
    "S001": ("operationId is missing or duplicated", "operationId absent ou en double"),
    "S002": ("collection GET lacks the paging/selection parameters {missing}",
             "le GET de collection n'a pas les paramètres de pagination/sélection {missing}"),
    "S003": ("collection GET 200 does not declare the count headers {missing}",
             "la réponse 200 du GET de collection ne déclare pas les en-têtes de comptage {missing}"),
    "S004": ("entity schema '{name}' lacks {missing}",
             "le schéma d'entité '{name}' n'a pas {missing}"),
    "S005": ("operation does not declare the error responses {missing}",
             "l'opération ne déclare pas les réponses d'erreur {missing}"),
    "S006": ("no /hub registration endpoint for event notifications",
             "aucun point d'inscription /hub pour les notifications d'événements"),
    "S007": ("info.version is missing", "info.version est absent"),
    "S008": ("operation has neither summary nor description",
             "l'opération n'a ni résumé ni description"),
}


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    where: str
    params: tuple = ()

    def message(self, lang="en"):
        text = dict(self.params).get("message", self.rule)  # rules outside the core carry their own text
        en, fr = MESSAGES.get(self.rule, (text, text))
        return (fr if lang == "fr" else en).format(**dict(self.params))


def _names(doc, params):
    return {resolve(doc, p).get("name") for p in params}


def _is_collection_get(path, method):
    return method == "get" and not path.rstrip("/").endswith("}")


def s001_operation_ids(doc):
    seen, out = set(), []
    for path, method, op in operations(doc):
        oid = op.get("operationId")
        if not oid or oid in seen:
            out.append(Finding("S001", ERROR if oid else WARN, f"{method.upper()} {path}"))
        seen.add(oid)
    return out


def s002_paging(doc):
    out = []
    for path, method, op in operations(doc):
        if _is_collection_get(path, method) and "{" not in path.rsplit("/", 1)[-1]:
            missing = sorted({"fields", "offset", "limit"} - _names(doc, op["parameters"]))
            if missing:
                out.append(Finding("S002", WARN, f"GET {path}", (("missing", ", ".join(missing)),)))
    return out


def s003_count_headers(doc):
    out = []
    for path, method, op in operations(doc):
        if _is_collection_get(path, method):
            ok = resolve(doc, (op.get("responses") or {}).get("200", {}))
            present = {str(h).lower() for h in (ok.get("headers") or {})}  # header names are case-insensitive
            missing = sorted(h for h in ("X-Total-Count", "X-Result-Count") if h.lower() not in present)
            if ok and missing:
                out.append(Finding("S003", WARN, f"GET {path}", (("missing", ", ".join(missing)),)))
    return out


def s004_entities(doc):
    out = []
    for name, schema in schemas(doc).items():
        if name.endswith("Event"):  # notification payloads do not follow the entity pattern in the observed files
            continue
        props = properties(doc, schema)
        if "href" in props:
            missing = [key for key in ("id", "@type") if key not in props]
            if missing:
                out.append(Finding("S004", WARN, f"schema {name}", (("name", name), ("missing", ", ".join(missing)))))
    return out


def s005_errors(doc):
    out = []
    for path, method, op in operations(doc):
        codes = set(response_codes(op))
        need = {"400", "500"} | ({"404"} if "{" in path else set())
        if "default" in codes:
            continue
        missing = sorted(need - codes)
        if missing:
            out.append(Finding("S005", WARN, f"{method.upper()} {path}", (("missing", ", ".join(missing)),)))
    return out


def s006_hub(doc):
    hub = doc["paths"].get("/hub")
    if isinstance(hub, dict) and "post" in hub:
        return []
    return [Finding("S006", INFO, "paths")]


def s007_version(doc):
    info = doc.get("info")
    return [] if isinstance(info, dict) and info.get("version") else [Finding("S007", WARN, "info")]


def s008_description(doc):
    return [Finding("S008", INFO, f"{method.upper()} {path}")
            for path, method, op in operations(doc) if not (op.get("summary") or op.get("description"))]


RULES = (s001_operation_ids, s002_paging, s003_count_headers, s004_entities,
         s005_errors, s006_hub, s007_version, s008_description)


def lint(doc, extra_rules=()):
    """Run the community rules plus any rule functions the caller supplies."""
    findings = []
    for rule in tuple(RULES) + tuple(extra_rules):
        findings.extend(rule(doc))
    return sorted(findings, key=lambda f: (f.rule, f.where))
