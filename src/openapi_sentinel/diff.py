"""Compare two versions of one API description and list changes that can break callers."""
from dataclasses import dataclass

from .core import deep_properties, operations, resolve

BREAKING = {
    "D001": ("path removed", "chemin supprimé"),
    "D002": ("operation removed", "opération supprimée"),
    "D003": ("new required input: {detail}", "nouvelle entrée obligatoire : {detail}"),
    "D004": ("success response removed: {detail}", "réponse de succès supprimée : {detail}"),
    "D005": ("response field removed: {detail}", "champ de réponse supprimé : {detail}"),
    "D006": ("type changed: {detail}", "type modifié : {detail}"),
}


@dataclass(frozen=True)
class Change:
    rule: str
    where: str
    detail: str = ""

    def message(self, lang="en"):
        en, fr = BREAKING[self.rule]
        return (fr if lang == "fr" else en).format(detail=self.detail)


def _request_inputs(doc, op):
    items = {}
    for raw in op["parameters"]:
        p = resolve(doc, raw)
        if p.get("in") == "body":
            for name, meta in deep_properties(doc, p.get("schema", {})).items():
                items[f"body.{name}"] = meta
        elif p.get("name"):
            items[f"{p.get('in', '?')}.{p['name']}"] = {"type": p.get("type") or "?", "required": bool(p.get("required"))}
    content = resolve(doc, op.get("requestBody", {})).get("content") or {}
    for media in content.values():
        for name, meta in deep_properties(doc, (media or {}).get("schema", {})).items():
            items[f"body.{name}"] = meta
        break
    return items


def _responses(doc, op):
    out = {}
    for code, raw in (op.get("responses") or {}).items():
        code = str(code)
        if not code.startswith("2"):
            continue
        response = resolve(doc, raw)
        schema = response.get("schema")
        if schema is None:
            for media in (response.get("content") or {}).values():
                schema = (media or {}).get("schema")
                break
        out[code] = deep_properties(doc, schema or {})
    return out


def compare(old, new):
    changes = []
    old_ops = {(p, m): op for p, m, op in operations(old)}
    new_ops = {(p, m): op for p, m, op in operations(new)}
    for path in old["paths"]:
        if path not in new["paths"]:
            changes.append(Change("D001", path))
    for (path, method), op in old_ops.items():
        where = f"{method.upper()} {path}"
        if (path, method) not in new_ops:
            if path in new["paths"]:
                changes.append(Change("D002", where))
            continue
        other = new_ops[(path, method)]
        before, after = _request_inputs(old, op), _request_inputs(new, other)
        for key, meta in after.items():
            top_level = not key.startswith("body.") or (key.count(".") == 1 and "[]" not in key)
            if top_level and meta["required"] and not before.get(key, {}).get("required"):
                changes.append(Change("D003", where, key))
            if key in before and before[key]["type"] != meta["type"] and "?" not in (before[key]["type"], meta["type"]):
                changes.append(Change("D006", where, f"{key}: {before[key]['type']} -> {meta['type']}"))
        resp_before, resp_after = _responses(old, op), _responses(new, other)
        for code, fields in resp_before.items():
            if code not in resp_after:
                changes.append(Change("D004", where, code))
                continue
            for name, meta in fields.items():
                if name not in resp_after[code]:
                    changes.append(Change("D005", where, f"{code} {name}"))
                elif meta["type"] != resp_after[code][name]["type"] and "?" not in (meta["type"], resp_after[code][name]["type"]):
                    changes.append(Change("D006", where, f"{code} {name}: {meta['type']} -> {resp_after[code][name]['type']}"))
    return sorted(changes, key=lambda c: (c.rule, c.where, c.detail))
