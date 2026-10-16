# Adding rules from outside

[Version française](extending.fr.md)

`openapi-sentinel lint` loads rule functions from any installed package that registers an entry point in the group `openapi_sentinel.rule_packs`. The entry point must resolve to a list (or tuple) of functions.

A rule function takes the loaded description (a `dict`) and returns a list of `openapi_sentinel.rules.Finding`:

```python
from openapi_sentinel.rules import Finding, WARN

def no_trailing_slash(doc):
    return [Finding("X001", WARN, path, (("message", "path ends with a slash"),))
            for path in doc["paths"] if path.endswith("/") and path != "/"]

RULES = [no_trailing_slash]
```

```toml
# pyproject.toml of your own package
[project.entry-points."openapi_sentinel.rule_packs"]
mypack = "mypack:RULES"
```

The core only has translated messages for its own ids (`S001` to `S008`); a custom finding passes its text as the `message` parameter, as above. A pack that raises on import is ignored with a warning and the core result is still printed.

Packs run with your permissions. Install only code you trust.
