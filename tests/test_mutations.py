"""Deterministic fixture mutations through the real CLI parser and file loader."""
import contextlib
import copy
import io
import json
import random
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from openapi_sentinel import cli

SEED = 20261019
COUNT = 3000
BUDGET_SECONDS = 120  # a guard against hangs: the test is about robustness, and slower machines take 2x CI
KINDS = ('delete', 'null', 'number', 'list', 'dict', 'string', 'duplicate', 'empty', 'truncate')


def containers(value):
    result = []
    if isinstance(value, (dict, list)):
        result.append(value)
        for child in value.values() if isinstance(value, dict) else value:
            result.extend(containers(child))
    return result


def mutate(original, kind, rng):
    value = copy.deepcopy(original)
    nodes = containers(value)
    if kind == 'truncate':
        text = json.dumps(value, ensure_ascii=False)
        return text[:rng.randrange(len(text))]
    if kind == 'delete':
        target = rng.choice([n for n in nodes if isinstance(n, dict) and n])
        del target[rng.choice(list(target))]
    elif kind == 'duplicate':
        target = rng.choice([n for n in nodes if isinstance(n, list) and n])
        target.append(copy.deepcopy(rng.choice(target)))
    elif kind == 'empty':
        rng.choice([n for n in nodes if isinstance(n, dict) and n]).clear()
    else:
        target = rng.choice([n for n in nodes if n])
        key = rng.choice(list(target)) if isinstance(target, dict) else rng.randrange(len(target))
        replacements = {'null': None, 'number': 42, 'list': [None, 42],
                        'dict': {'unexpected': None}, 'string': 'mutated {value}'}
        target[key] = replacements[kind]
    return json.dumps(value, ensure_ascii=False)


class MutationTests(unittest.TestCase):
    def test_fixture_mutations_never_escape_cli(self):
        fixtures = sorted((ROOT / 'fixtures').glob('*.json'))
        originals = [json.loads(p.read_text(encoding='utf-8')) for p in fixtures]
        self.assertTrue(originals)
        rng = random.Random(SEED)
        counts = {kind: 0 for kind in KINDS}
        exits = {0: 0, 1: 0, 2: 0}
        started = time.perf_counter()
        with tempfile.TemporaryDirectory() as tmp, patch.object(cli.metadata, 'entry_points', return_value=[]):
            mutated = Path(tmp) / 'mutated.json'
            bases = []
            for number, fixture in enumerate(fixtures):
                baseline = Path(tmp) / f"original-{number}.json"
                baseline.write_bytes(fixture.read_bytes())
                bases.append(baseline)
            with mutated.open("w", encoding="utf-8") as writer:
                for index in range(COUNT):
                    fixture_index = (index // len(KINDS)) % len(fixtures)
                    kind = KINDS[index % len(KINDS)]
                    text = mutate(originals[fixture_index], kind, rng)
                    writer.seek(0)
                    writer.write(text)
                    writer.truncate()
                    writer.flush()
                    counts[kind] += 1
                    base = str(bases[fixture_index])
                    commands = [('lint', str(mutated)), ('diff', base, str(mutated)), ('diff', str(mutated), base)]
                    for command in commands:
                        output, error = io.StringIO(), io.StringIO()
                        with self.subTest(index=index, kind=kind, command=command), contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                            code = cli.main(['--format', ('text', 'json', 'md', 'sarif')[index % 4],
                                             '--lang', ('en', 'fr')[(index // 4) % 2], *command])
                            self.assertIn(code, (0, 1, 2))
                            self.assertNotIn('Traceback', error.getvalue())
                            self.assertNotIn('Traceback', output.getvalue())
                            if code == 2:
                                self.assertTrue(error.getvalue().strip())
                            exits[code] += 1
        elapsed = time.perf_counter() - started
        self.assertEqual(sum(counts.values()), COUNT)
        self.assertEqual(sum(exits.values()), COUNT * 3)
        self.assertTrue(all(counts.values()))
        print(f'Mutations: seed={SEED}, inputs={COUNT}, CLI calls={sum(exits.values())}, '
              f'kinds={counts}, exits={exits}, seconds={elapsed:.3f}')
        self.assertLess(elapsed, BUDGET_SECONDS, f'{COUNT} mutations took {elapsed:.3f}s')
