"""Command line: openapi-sentinel lint FILE | diff OLD NEW."""
import argparse
import json
import sys
from importlib import metadata

from .core import SentinelError, load
from .diff import compare
from .rules import ERROR, WARN, lint

PACK_GROUP = "openapi_sentinel.rule_packs"  # extension point: installed packs may add rule functions

LABELS = {
    "en": {"break": "BREAKING", "lint_head": "| Rule | Severity | Where | Message |", "diff_head": "| Rule | Where | Change |",
           "none_lint": "No findings.", "none_diff": "No breaking change found."},
    "fr": {"break": "RUPTURE", "lint_head": "| Règle | Gravité | Où | Message |", "diff_head": "| Règle | Où | Changement |",
           "none_lint": "Aucun constat.", "none_diff": "Aucune rupture détectée."},
}


def _extra_rules():
    rules = []
    for entry in metadata.entry_points(group=PACK_GROUP):
        try:
            rules.extend(entry.load())
        except Exception as error:  # a broken third-party pack must not hide the core result
            print(f"warning: rule pack {entry.name} ignored ({error})", file=sys.stderr)
    return rules


def _emit_lint(findings, args):
    if args.format == "json":
        print(json.dumps([{"rule": f.rule, "severity": f.severity, "where": f.where,
                           "message": f.message(args.lang)} for f in findings], ensure_ascii=False, indent=2))
    elif args.format == "md":
        print(LABELS[args.lang]["lint_head"] + "\n|---|---|---|---|")
        for f in findings:
            print(f"| {f.rule} | {f.severity} | `{f.where}` | {f.message(args.lang)} |")
    else:
        for f in findings:
            print(f"{f.severity.upper():5} {f.rule} {f.where}: {f.message(args.lang)}")
        if not findings:
            print(LABELS[args.lang]["none_lint"])


def _emit_diff(changes, args):
    if args.format == "json":
        print(json.dumps([{"rule": c.rule, "where": c.where, "detail": c.detail,
                           "message": c.message(args.lang)} for c in changes], ensure_ascii=False, indent=2))
    elif args.format == "md":
        print(LABELS[args.lang]["diff_head"] + "\n|---|---|---|")
        for c in changes:
            print(f"| {c.rule} | `{c.where}` | {c.message(args.lang)} |")
    else:
        for c in changes:
            print(f"{LABELS[args.lang]['break']} {c.rule} {c.where}: {c.message(args.lang)}")
        if not changes:
            print(LABELS[args.lang]["none_diff"])


def main(argv=None):
    parser = argparse.ArgumentParser(prog="openapi-sentinel", description="Lint and compare OpenAPI/Swagger descriptions. Offline, no network.")
    parser.add_argument("--lang", choices=("en", "fr"), default="en")
    parser.add_argument("--format", choices=("text", "json", "md"), default="text")
    sub = parser.add_subparsers(dest="command", required=True)
    p_lint = sub.add_parser("lint", help="check conventions")
    p_lint.add_argument("file")
    p_lint.add_argument("--fail-on", choices=("error", "warn", "never"), default="error")
    p_diff = sub.add_parser("diff", help="list breaking changes between two versions")
    p_diff.add_argument("old")
    p_diff.add_argument("new")
    args = parser.parse_args(argv)
    try:
        if args.command == "lint":
            findings = lint(load(args.file), _extra_rules())
            _emit_lint(findings, args)
            bad = {"error": (ERROR,), "warn": (ERROR, WARN), "never": ()}[args.fail_on]
            return 1 if any(f.severity in bad for f in findings) else 0
        changes = compare(load(args.old), load(args.new))
        _emit_diff(changes, args)
        return 1 if changes else 0
    except SentinelError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (TypeError, AttributeError, KeyError, ValueError) as error:  # structure the checks cannot walk
        print(f"error: malformed description ({type(error).__name__}: {error})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
