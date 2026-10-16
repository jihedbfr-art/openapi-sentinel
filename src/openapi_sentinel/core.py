"""Load an API description and walk it. Standard library only (YAML is optional)."""
import json
from pathlib import Path

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options", "trace")


class SentinelError(Exception):
    """A readable failure: bad file, bad syntax, unsupported input."""


def load(path):
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise SentinelError(f"cannot read {p}: {error.strerror or error}") from error
    if p.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml  # optional: only needed for YAML input
        except ImportError as error:
            raise SentinelError("YAML input needs PyYAML (pip install pyyaml), or convert the file to JSON") from error
        try:
            doc = yaml.safe_load(text)
        except yaml.YAMLError as error:
            raise SentinelError(f"invalid YAML in {p}: {error}") from error
    else:
        try:
            doc = json.loads(text)
        except ValueError as error:
            raise SentinelError(f"invalid JSON in {p}: {error}") from error
    if not isinstance(doc, dict) or not isinstance(doc.get("paths"), dict):
        raise SentinelError(f"{p} is not an OpenAPI/Swagger description (no 'paths' object)")
    if not (doc.get("swagger") or doc.get("openapi")):
        raise SentinelError(f"{p} declares neither 'swagger' nor 'openapi'")
    return doc


def resolve(doc, node, _depth=0):
    """Follow local $ref pointers; stop quietly on external or cyclic references."""
    while isinstance(node, dict) and "$ref" in node and _depth < 20:
        ref = node["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/"):
            return {}
        target = doc
        for part in ref[2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(target, dict) or part not in target:
                return {}
            target = target[part]
        node = target
        _depth += 1
    return node if isinstance(node, dict) else {}


def operations(doc):
    """Yield (path, method, operation) with path-level parameters merged in."""
    for path, item in doc["paths"].items():
        if not isinstance(item, dict):
            continue
        shared = item.get("parameters") or []
        if not isinstance(shared, list):
            raise SentinelError(f"'parameters' of path {path} must be a list")
        for method in HTTP_METHODS:
            op = item.get(method)
            if isinstance(op, dict):
                own = op.get("parameters") or []
                if not isinstance(own, list):
                    raise SentinelError(f"'parameters' of {method.upper()} {path} must be a list")
                if not isinstance(op.get("responses") or {}, dict):
                    raise SentinelError(f"'responses' of {method.upper()} {path} must be an object")
                merged = dict(op)
                merged["parameters"] = list(shared) + own
                yield path, method, merged


def schemas(doc):
    """Named schemas of the description (Swagger 2 definitions or OpenAPI 3 components)."""
    found = doc.get("definitions")
    if not isinstance(found, dict):
        found = (doc.get("components") or {}).get("schemas")
    return found if isinstance(found, dict) else {}


def properties(doc, schema, _seen=None, _depth=0):
    """Flatten an object schema (allOf merged, local refs followed) to {name: {type, required}}."""
    _seen = set() if _seen is None else _seen
    out = {}
    if _depth > 12 or not isinstance(schema, dict):
        return out
    if "$ref" in schema:
        if schema["$ref"] in _seen:
            return out
        _seen = _seen | {schema["$ref"]}
        return properties(doc, resolve(doc, schema), _seen, _depth + 1)
    for part in schema.get("allOf", []) or []:
        for name, meta in properties(doc, part, _seen, _depth + 1).items():
            if name in out and out[name]["required"]:
                meta = dict(meta, required=True)  # a field required by any branch stays required
            out[name] = meta
    required = set(schema.get("required") or []) if isinstance(schema.get("required"), list) else set()
    own = schema.get("properties")
    for name, sub in (own.items() if isinstance(own, dict) else ()):
        sub_resolved = resolve(doc, sub)
        out[name] = {"type": sub_resolved.get("type") or ("object" if sub_resolved.get("properties") or sub_resolved.get("allOf") else "?"),
                     "required": name in required, "schema": sub}
    for name in required:
        if name in out:
            out[name]["required"] = True
    return out


def type_of(doc, schema):
    node = resolve(doc, schema)
    return node.get("type") or ("object" if node.get("properties") or node.get("allOf") or node.get("additionalProperties") else "?")


def deep_properties(doc, schema, prefix="", _path=frozenset(), _depth=0):
    """Flatten a schema to {path: {type, required}}.

    Paths: a.b for nested objects, a[] for array elements, a{} for dictionary values, (root) for the
    body itself. Cyclic references are followed once.
    """
    out = {}
    if _depth > 8:
        return out
    top = resolve(doc, schema)
    if top.get("type") == "array" and isinstance(top.get("items"), dict):
        key = prefix.rstrip(".") + "[]"
        out[key] = {"type": type_of(doc, top["items"]), "required": False}
        out.update(deep_properties(doc, top["items"], key + ".", _path, _depth + 1))
        return out
    if not prefix:
        out["(root)"] = {"type": type_of(doc, schema), "required": False}
    for name, meta in properties(doc, schema).items():
        key = prefix + name
        out[key] = {"type": meta["type"], "required": meta["required"]}
        node = meta["schema"]
        ref = node.get("$ref") if isinstance(node, dict) else None
        if ref in _path:
            continue
        out.update(deep_properties(doc, node, key + ".", _path | ({ref} if ref else set()), _depth + 1))
    extra = top.get("additionalProperties")
    if isinstance(extra, dict):
        key = prefix.rstrip(".") + "{}" if prefix else "{}"
        out[key] = {"type": type_of(doc, extra), "required": False}
        out.update(deep_properties(doc, extra, key + ".", _path, _depth + 1))
    return out


def response_codes(op):
    return [str(code) for code in (op.get("responses") or {})]
