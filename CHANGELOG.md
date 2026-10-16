# Changelog

## 0.1.1

Fix: `diff` now compares nested object properties and the elements of array responses (0.1.0 only looked at top-level fields of single objects and missed changes inside collections). New required inputs are reported only for top-level body fields. 20 tests.

## 0.1.0

First public version: eight convention checks (`lint`), six breaking-change checks (`diff`), English and French messages, text/JSON/Markdown output, rule-pack entry point, 18 tests.
