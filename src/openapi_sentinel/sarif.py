"""SARIF 2.1.0 reports with file and logical locations, without guessed lines."""
from pathlib import Path
from urllib.parse import quote

from . import __version__

SCHEMA = "https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/schemas/sarif-schema-2.1.0.json"
DESCRIPTIONS = {
    "S001": "Missing or duplicate operationId",
    "S002": "Missing collection paging or selection parameters",
    "S003": "Missing collection count headers",
    "S004": "Missing entity identity fields",
    "S005": "Missing error responses",
    "S006": "Missing notification registration endpoint",
    "S007": "Missing API version",
    "S008": "Missing operation description",
    "D001": "Removed path", "D002": "Removed operation",
    "D003": "New required input", "D004": "Removed success response",
    "D005": "Removed response field", "D006": "Changed field type",
}
LEVELS = {"error": "error", "warn": "warning", "info": "note"}


def artifact_uri(filename):
    """Prefer a cwd-relative URI; retain an absolute URI for external files."""
    path = Path(filename).resolve()
    try:
        return quote(path.relative_to(Path.cwd().resolve()).as_posix(), safe="/")
    except ValueError:
        return path.as_uri()


def report(findings, filename, lang="en", *, old=None):
    """For diffs, removals point to old; new requirements and types point to new."""
    prefix = "D" if old is not None else "S"
    rules = {key: value for key, value in DESCRIPTIONS.items() if key.startswith(prefix)}
    results = []
    uris = {}
    for finding in findings:
        rules.setdefault(finding.rule, "External rule " + finding.rule)
        source = old if old is not None and finding.rule in {"D001", "D002", "D004", "D005"} else filename
        if source not in uris:
            uris[source] = artifact_uri(source)
        logical = finding.where
        if old is not None and finding.detail:
            logical += " / " + finding.detail
        results.append({
            "ruleId": finding.rule,
            "level": "error" if old is not None else LEVELS[finding.severity],
            "message": {"text": finding.message(lang)},
            "locations": [{
                "physicalLocation": {"artifactLocation": {"uri": uris[source]}},
                "logicalLocations": [{"fullyQualifiedName": logical}],
            }],
        })
    return {"$schema": SCHEMA, "version": "2.1.0", "runs": [{
        "tool": {"driver": {"name": "openapi-sentinel", "version": __version__,
                            "rules": [{"id": key, "shortDescription": {"text": value}}
                                      for key, value in sorted(rules.items())]}},
        "results": results,
    }]}
