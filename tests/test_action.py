import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
import run_action


class ActionTests(unittest.TestCase):
    def run_case(self, *, spec="offer-api.json", mode="lint", baseline="", language="en", fail_on="error", report="report.sarif", content=None, input_name="input.json"):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / input_name
            source.write_text((ROOT / "fixtures" / spec).read_text(encoding="utf-8") if content is None else content, encoding="utf-8")
            old = workspace / "old.json"
            if baseline:
                old.write_bytes((ROOT / "fixtures" / baseline).read_bytes())
            output = workspace / "outputs.txt"
            environment = {"GITHUB_WORKSPACE": str(workspace), "GITHUB_OUTPUT": str(output), "SENTINEL_SPEC": str(source), "SENTINEL_MODE": mode, "SENTINEL_BASELINE": str(old) if baseline else "", "SENTINEL_LANG": language, "SENTINEL_FAIL_ON": fail_on, "SENTINEL_REPORT": report}
            with patch.dict(os.environ, environment), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = run_action.main()
            data = json.loads((workspace / report).read_text(encoding="utf-8")) if (workspace / report).is_file() and report != input_name else None
            return code, data, output.read_text(encoding="utf-8"), source.read_text(encoding="utf-8")

    def test_input_names_with_spaces_and_metacharacters_are_literal(self):
        self.assertEqual(self.run_case(input_name="api; echo injected.json")[0], 0)

    def test_inputs_cannot_read_outside_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            outside = root / "outside.json"
            inside = workspace / "inside.json"
            for target in (inside, outside):
                target.write_bytes((ROOT / "fixtures" / "offer-api.json").read_bytes())
            for mode in ("lint", "diff"):
                with self.subTest(mode=mode):
                    environment = {"GITHUB_WORKSPACE": str(workspace), "GITHUB_OUTPUT": str(workspace / "outputs.txt"), "SENTINEL_SPEC": str(outside if mode == "lint" else inside), "SENTINEL_MODE": mode, "SENTINEL_BASELINE": str(outside), "SENTINEL_REPORT": "report.sarif"}
                    with patch.dict(os.environ, environment), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        self.assertEqual(run_action.main(), 2)

    def test_valid_lint_produces_empty_sarif(self):
        code, report, outputs, _ = self.run_case()
        self.assertEqual(code, 0)
        self.assertEqual(report["runs"][0]["results"], [])
        self.assertIn("exit-code=0", outputs)
        self.assertIn("sarif-file=report.sarif", outputs)

    def test_weak_input_fails_and_retains_bilingual_reports(self):
        for language in ("en", "fr"):
            with self.subTest(language=language):
                code, report, outputs, _ = self.run_case(spec="offer-api-weak.json", language=language)
                self.assertEqual(code, 1)
                self.assertEqual(len(report["runs"][0]["results"]), 9)
                self.assertIn("findings=9", outputs)

    def test_diff_breaking_fails(self):
        code, report, _, _ = self.run_case(spec="offer-api-v2.json", mode="diff", baseline="offer-api-v1.json")
        self.assertEqual(code, 1)
        self.assertEqual(len(report["runs"][0]["results"]), 7)

    def test_diff_unchanged_passes(self):
        code, report, _, _ = self.run_case(spec="offer-api-v1.json", mode="diff", baseline="offer-api-v1.json")
        self.assertEqual((code, report["runs"][0]["results"]), (0, []))

    def test_never_threshold_keeps_findings_but_passes(self):
        code, report, _, _ = self.run_case(spec="offer-api-weak.json", fail_on="never")
        self.assertEqual(code, 0)
        self.assertTrue(report["runs"][0]["results"])

    def test_malformed_input_returns_two_without_report(self):
        code, report, outputs, _ = self.run_case(content="not JSON")
        self.assertEqual((code, report), (2, None))
        self.assertIn("exit-code=2", outputs)
        self.assertNotIn("sarif-file=", outputs)

    def test_diff_requires_baseline(self):
        self.assertEqual(self.run_case(mode="diff")[0], 2)

    def test_invalid_mode_is_rejected(self):
        self.assertEqual(self.run_case(mode="lint; echo injected")[0], 2)

    def test_report_cannot_overwrite_input(self):
        code, _, _, source = self.run_case(report="input.sarif", input_name="input.sarif")
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(source)["swagger"], "2.0")

    def test_report_must_stay_in_workspace(self):
        self.assertEqual(self.run_case(report="../outside.sarif")[0], 2)

    def test_report_name_cannot_inject_outputs(self):
        self.assertEqual(self.run_case(report="bad\nexit-code=0.sarif")[0], 2)

    def test_report_may_contain_spaces_and_shell_metacharacters(self):
        code, report, outputs, _ = self.run_case(report="with space;echo test.sarif")
        self.assertEqual(code, 0)
        self.assertEqual(report["version"], "2.1.0")
        self.assertIn("sarif-file=with space;echo test.sarif", outputs)


if __name__ == "__main__":
    unittest.main()
