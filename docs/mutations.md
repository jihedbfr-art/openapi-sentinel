# Mutation coverage

[Version française](mutations.fr.md)

Run `python -m unittest discover -s tests -p test_mutations.py` from the repository root. The test uses only the standard library and seed `20261019`. It creates 3,000 mutated inputs from the four JSON fixtures and makes 9,000 calls to the real CLI entry point: lint, original-to-mutated diff, and mutated-to-original diff. The parser, disk loader, checks and output serialization all run. Installed rule-pack discovery is isolated so local plugins cannot change the corpus.

The nine mutation families are key deletion; replacement with null, a number, a list, an object or a string; list-item duplication; object clearing; and text truncation. Every fixture receives every family. The test rotates text, JSON, Markdown and SARIF output and English/French messages. Each call must return 0, 1 or 2; code 2 requires nonempty stderr, and neither output stream may contain a traceback. Unexpected exceptions fail the test. The complete mutation run must finish within 120 seconds, a guard against hangs (CI takes a few seconds; a busy Windows machine took 20 to 40).

On Windows with Python 3.12.0, the checked run completed in 26.997 seconds: 5,710 calls returned 0, 1,950 returned 1, and 1,340 returned 2. No unhandled exception was found, so there is no minimized crash input or crash fix to report.

This is a bounded reproducible corpus, not a proof for every input. Calls run in process rather than starting 9,000 interpreters. There are no YAML fixtures in this repository, so truncation covers JSON only. YAML parsing, third-party rule packs, arbitrary nesting depth and external service behavior are outside this test. Runtime depends on the machine; the 30-second assertion remains active.

Earlier local attempts exceeded the budget; its threshold was not changed. The CLI reuses the parser definition and resolves a URI once per source in each report. SARIF is emitted without indentation, with the same JSON structure. The temporary writer remains open, flushed before every real CLI read; baselines are exact fixture copies in that same temporary directory. No call or assertion was removed.
