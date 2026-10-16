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


def _media_schemas(media_map):
    """(label, schema) for each media type; the JSON one (or the first) has an empty label."""
    names = [m for m in media_map if isinstance(media_map[m], dict) or media_map[m] is None]
    names.sort(key=lambda m: (m != "application/json",))
    return [("" if k == 0 else f"<{m}>", (media_map[m] or {}).get("schema", {})) for k, m in enumerate(names)]


def _parent(key):
    base = key[:-2] if key.endswith("[]") else key
    return base.rsplit(".", 1)[0] if "." in base else None


def _request_inputs(doc, op):
    items = {}
    for raw in op["parameters"]:
        p = resolve(doc, raw)
        if p.get("in") == "body":
            items["body"] = {"type": "object", "required": bool(p.get("required"))}
            for name, meta in deep_properties(doc, p.get("schema", {})).items():
                items[f"body.{name}"] = meta
        elif p.get("name"):
            kind = p.get("type") or resolve(doc, p.get("schema", {})).get("type") or "?"
            items[f"{p.get('in', '?')}.{p['name']}"] = {"type": kind, "required": bool(p.get("required"))}
    request = resolve(doc, op.get("requestBody", {}))
    content = request.get("content") or {}
    if content:
        items["body"] = {"type": "object", "required": bool(request.get("required"))}
    for label, schema in _media_schemas(content):
        for name, meta in deep_properties(doc, schema).items():
            items[f"body{label}.{name}"] = meta
    return items


def _responses(doc, op):
    out = {}
    for code, raw in (op.get("responses") or {}).items():
        code = str(code)
        if not code.startswith("2"):
            continue
        response = resolve(doc, raw)
        if "schema" in response:
            out[code] = deep_properties(doc, response["schema"] or {})
        for label, schema in _media_schemas(response.get("content") or {}):
            out[code + label] = deep_properties(doc, schema or {})
        out.setdefault(code, {})
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
            nested = key.startswith("body") and "." in key
            known = not nested or key in before or _parent(key) in before  # a wholly new optional object may bring required children
            if known and meta["required"] and not before.get(key, {}).get("required"):
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
