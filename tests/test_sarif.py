import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
from openapi_sentinel import cli, __version__
from openapi_sentinel.core import load
from openapi_sentinel.diff import compare, Change
from openapi_sentinel.rules import lint, Finding
from openapi_sentinel.sarif import artifact_uri, report

FIX = ROOT / 'fixtures'


class SarifTests(unittest.TestCase):
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), patch.object(cli, '_extra_rules', return_value=[]):
            code = cli.main(['--format', 'sarif', *map(str, args)])
        return code, out.getvalue(), err.getvalue()

    def test_lint_results_match_findings_and_levels(self):
        code, out, err = self.run_cli('lint', FIX / 'offer-api-weak.json')
        data = json.loads(out)
        self.assertEqual((code, err, data['version']), (1, '', '2.1.0'))
        run = data['runs'][0]
        self.assertEqual(run['tool']['driver']['version'], __version__)
        findings = lint(load(FIX / 'offer-api-weak.json'))
        self.assertEqual(len(run['results']), len(findings))
        self.assertEqual({r['id'] for r in run['tool']['driver']['rules']}, {f'S00{i}' for i in range(1, 9)})
        self.assertEqual({r['level'] for r in run['results']}, {'error', 'warning', 'note'})
        for result, finding in zip(run['results'], findings):
            self.assertEqual(result['ruleId'], finding.rule)
            self.assertEqual(result['level'], {'error': 'error', 'warn': 'warning', 'info': 'note'}[finding.severity])
            self.assertEqual(result['message']['text'], finding.message())
            location = result['locations'][0]
            self.assertEqual(location['logicalLocations'][0]['fullyQualifiedName'], finding.where)
            self.assertNotIn('region', location['physicalLocation'])

    def test_empty_lint_and_diff(self):
        for args in [('lint', FIX / 'offer-api.json'), ('diff', FIX / 'offer-api-v1.json', FIX / 'offer-api-v1.json')]:
            with self.subTest(args=args):
                code, out, err = self.run_cli(*args)
                self.assertEqual((code, err), (0, ''))
                self.assertEqual(json.loads(out)['runs'][0]['results'], [])

    def test_french_lint_preserves_english_rule_descriptions(self):
        _, out, _ = self.run_cli('--lang', 'fr', 'lint', FIX / 'offer-api-weak.json')
        run = json.loads(out)['runs'][0]
        self.assertIn('info.version est absent', [r['message']['text'] for r in run['results']])
        self.assertEqual(next(r for r in run['tool']['driver']['rules'] if r['id'] == 'S007')['shortDescription']['text'], 'Missing API version')

    def test_diff_french_levels_counts_and_source_files(self):
        old, new = FIX / 'offer-api-v1.json', FIX / 'offer-api-v2.json'
        code, out, err = self.run_cli('--lang', 'fr', 'diff', old, new)
        self.assertEqual((code, err), (1, ''))
        run = json.loads(out)['runs'][0]
        changes = compare(load(old), load(new))
        self.assertEqual(len(run['results']), len(changes))
        self.assertEqual(len(run['tool']['driver']['rules']), 6)
        for result, change in zip(run['results'], changes):
            self.assertEqual(result['level'], 'error')
            self.assertEqual(result['message']['text'], change.message('fr'))
            source = old if change.rule in {'D001', 'D002', 'D004', 'D005'} else new
            self.assertEqual(result['locations'][0]['physicalLocation']['artifactLocation']['uri'], artifact_uri(source))
            self.assertIn(change.where, result['locations'][0]['logicalLocations'][0]['fullyQualifiedName'])

    def test_removed_operation_points_to_old(self):
        result = report([Change('D002', 'GET /x')], 'new.json', old='old.json')['runs'][0]['results'][0]
        self.assertEqual(result['locations'][0]['physicalLocation']['artifactLocation']['uri'], 'old.json')

    def test_uri_escapes_special_characters_and_is_relative(self):
        self.assertEqual(artifact_uri(Path.cwd() / 'fixtures' / 'été #1%.json'), 'fixtures/%C3%A9t%C3%A9%20%231%25.json')
        self.assertNotIn('\\', artifact_uri(FIX / 'offer-api.json'))

    def test_external_absolute_uri(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'other #1.json'
            self.assertEqual(artifact_uri(path), path.resolve().as_uri())

    def test_external_rules_have_descriptors_and_keep_messages(self):
        data = report([Finding('X001', 'warn', '/x', (('message', 'Custom check'),))], 'api.json')
        run = data['runs'][0]
        self.assertIn({'id': 'X001', 'shortDescription': {'text': 'External rule X001'}}, run['tool']['driver']['rules'])
        self.assertEqual(run['results'][0]['message']['text'], 'Custom check')

    def test_fail_on_never_keeps_findings(self):
        code, out, err = self.run_cli('lint', FIX / 'offer-api-weak.json', '--fail-on', 'never')
        self.assertEqual((code, err), (0, ''))
        self.assertTrue(json.loads(out)['runs'][0]['results'])

    def test_input_error_remains_stderr_and_exit_two(self):
        code, out, err = self.run_cli('lint', FIX / 'missing.json')
        self.assertEqual((code, out), (2, ''))
        self.assertIn('cannot read', err)
