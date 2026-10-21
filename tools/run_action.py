"""Run the installed CLI for a composite action without shell interpolation."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys

from openapi_sentinel.cli import main as run_cli


def outputs(values):
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8", newline="\n") as stream:
            for key, value in values.items():
                stream.write(f"{key}={value}\n")


def main():
    try:
        workspace = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd())).resolve()
        mode = os.environ.get("SENTINEL_MODE", "lint")
        language = os.environ.get("SENTINEL_LANG", "en")
        threshold = os.environ.get("SENTINEL_FAIL_ON", "error")
        spec = os.environ.get("SENTINEL_SPEC", "")
        baseline = os.environ.get("SENTINEL_BASELINE", "")
        report_name = os.environ.get("SENTINEL_REPORT", "openapi-sentinel.sarif")
        if mode not in ("lint", "diff") or language not in ("en", "fr") or threshold not in ("error", "warn", "never"):
            raise ValueError("unsupported mode, language or threshold")
        if not spec or (mode == "diff" and not baseline):
            raise ValueError("spec is required; diff also requires baseline")
        if not report_name or any(character in report_name for character in "\r\n"):
            raise ValueError("report must be a single-line path")
        report = (workspace / report_name).resolve()
        relative_report = report.relative_to(workspace).as_posix()
        if report.suffix != ".sarif":
            raise ValueError("report must end in .sarif")
        source = (workspace / spec).resolve()
        old = (workspace / baseline).resolve() if baseline else None
        source.relative_to(workspace)
        if old is not None:
            old.relative_to(workspace)
        if report in (source, old):
            raise ValueError("report must not overwrite an input")
        arguments = ["--lang", language, "--format", "sarif", mode]
        arguments += [str(old), str(source)] if mode == "diff" else [str(source), "--fail-on", threshold]
        captured = io.StringIO()
        with redirect_stdout(captured):
            code = run_cli(arguments)
        if code not in (0, 1):
            outputs({"exit-code": 2})
            return 2
        data = json.loads(captured.getvalue())
        runs = data.get("runs", [])
        if data.get("version") != "2.1.0" or len(runs) != 1 or not isinstance(runs[0].get("results"), list):
            raise ValueError("CLI did not return a SARIF 2.1.0 results list")
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(captured.getvalue(), encoding="utf-8")
        count = len(runs[0]["results"])
        outputs({"exit-code": code, "sarif-file": relative_report, "findings": count})
        print(f"{mode}: {count} findings, exit {code}; report: {relative_report}")
        return code
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        outputs({"exit-code": 2})
        return 2


if __name__ == "__main__":
    sys.exit(main())
