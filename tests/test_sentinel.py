import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from openapi_sentinel import cli  # noqa: E402
from openapi_sentinel.core import SentinelError, load  # noqa: E402
from openapi_sentinel.diff import compare  # noqa: E402
from openapi_sentinel.rules import Finding, lint  # noqa: E402

FIX = ROOT / "fixtures"


def rules_of(findings):
    return {f.rule for f in findings}


class LintTests(unittest.TestCase):
    def test_conforming_fixture_has_no_findings(self):
        self.assertEqual(lint(load(FIX / "offer-api.json")), [])

    def test_weak_fixture_triggers_every_rule(self):
        self.assertEqual(rules_of(lint(load(FIX / "offer-api-weak.json"))),
                         {"S001", "S002", "S003", "S004", "S005", "S006", "S007", "S008"})

    def test_duplicate_operation_id_is_an_error(self):
        severities = {f.severity for f in lint(load(FIX / "offer-api-weak.json")) if f.rule == "S001"}
        self.assertIn("error", severities)

    def test_event_schemas_are_exempt_from_entity_rule(self):
        doc = load(FIX / "offer-api.json")
        doc["definitions"]["OfferCreateEvent"] = {"type": "object", "properties": {"href": {"type": "string"}}}
        self.assertEqual(lint(doc), [])

    def test_refs_in_parameters_are_followed(self):
        doc = load(FIX / "offer-api-weak.json")
        doc["parameters"] = {"Offset": {"name": "offset", "in": "query", "type": "integer"},
                             "Limit": {"name": "limit", "in": "query", "type": "integer"}}
        doc["paths"]["/offer"]["get"]["parameters"] += [{"$ref": "#/parameters/Offset"}, {"$ref": "#/parameters/Limit"}]
        self.assertNotIn("S002", rules_of(lint(doc)))

    def test_openapi3_description_is_supported(self):
        doc = {"openapi": "3.0.3", "info": {"title": "t", "version": "1"},
               "paths": {"/offer": {"get": {"operationId": "a", "summary": "s",
                                            "parameters": [{"name": n, "in": "query"} for n in ("fields", "offset", "limit")],
                                            "responses": {"200": {"description": "ok", "headers": {"X-Total-Count": {}, "X-Result-Count": {}}},
                                                          "400": {"description": "e"}, "500": {"description": "e"}}}},
                         "/hub": {"post": {"operationId": "b", "summary": "s",
                                           "responses": {"201": {"description": "ok"}, "400": {"description": "e"}, "500": {"description": "e"}}}}},
               "components": {"schemas": {}}}
        self.assertEqual(lint(doc), [])

    def test_extra_rule_functions_are_run(self):
        extra = lambda doc: [Finding("S007", "info", "custom")]  # noqa: E731
        self.assertEqual(len(lint(load(FIX / "offer-api.json"), [extra])), 1)

    def test_custom_rule_message_falls_back_to_its_own_text(self):
        finding = Finding("X001", "warn", "/a/", (("message", "path ends with a slash"),))
        self.assertEqual(finding.message("fr"), "path ends with a slash")

    def test_cyclic_schema_does_not_hang(self):
        doc = load(FIX / "offer-api.json")
        doc["definitions"]["Node"] = {"type": "object", "properties": {"href": {"type": "string"}, "next": {"$ref": "#/definitions/Node"}}}
        self.assertIn("S004", rules_of(lint(doc)))


class DiffTests(unittest.TestCase):
    def test_identical_versions_have_no_change(self):
        doc = load(FIX / "offer-api.json")
        self.assertEqual(compare(doc, copy.deepcopy(doc)), [])

    def test_reference_pair_reports_each_break(self):
        got = {(c.rule, c.where, c.detail) for c in compare(load(FIX / "offer-api-v1.json"), load(FIX / "offer-api-v2.json"))}
        self.assertEqual(got, {("D001", "/hub", ""), ("D003", "POST /offer", "body.credits"),
                               ("D004", "GET /offer/{id}", "200"), ("D005", "POST /offer", "201 credits"),
                               ("D005", "GET /offer", "200 [].credits"),
                               ("D006", "POST /offer", "201 name: string -> integer"),
                               ("D006", "GET /offer", "200 [].name: string -> integer")})

    def test_additive_change_is_not_breaking(self):
        old = load(FIX / "offer-api.json")
        new = copy.deepcopy(old)
        new["definitions"]["Offer"]["properties"]["colour"] = {"type": "string"}
        new["paths"]["/extra"] = {"get": {"operationId": "x", "responses": {"200": {"description": "ok"}}}}
        self.assertEqual(compare(old, new), [])

    def test_nested_and_collection_response_fields_are_compared(self):
        old = load(FIX / "offer-api.json")
        old["definitions"]["Offer"]["properties"]["owner"] = {"$ref": "#/definitions/Owner"}
        old["definitions"]["Owner"] = {"type": "object", "properties": {"email": {"type": "string"}, "tags": {
            "type": "array", "items": {"type": "object", "properties": {"label": {"type": "string"}}}}}}
        new = copy.deepcopy(old)
        del new["definitions"]["Owner"]["properties"]["email"]
        del new["definitions"]["Owner"]["properties"]["tags"]["items"]["properties"]["label"]
        got = {c.detail for c in compare(old, new) if c.rule == "D005"}
        self.assertIn("200 [].owner.email", got)  # GET /offer returns an array of Offer
        self.assertIn("200 owner.email", got)     # GET /offer/{id} returns one Offer
        self.assertIn("200 [].owner.tags[].label", got)

    def test_required_field_nested_in_optional_object_is_not_a_new_required_input(self):
        old = load(FIX / "offer-api.json")
        old["definitions"]["OfferCreate"]["properties"]["contact"] = {"type": "object", "properties": {"mail": {"type": "string"}}}
        new = copy.deepcopy(old)
        new["definitions"]["OfferCreate"]["properties"]["contact"]["required"] = ["mail"]
        self.assertEqual(compare(old, new), [])

    def test_removed_operation_with_path_kept(self):
        old = load(FIX / "offer-api.json")
        new = copy.deepcopy(old)
        del new["paths"]["/offer"]["post"]
        self.assertEqual([(c.rule, c.where) for c in compare(old, new)], [("D002", "POST /offer")])

    def test_new_required_parameter_is_breaking(self):
        old = load(FIX / "offer-api.json")
        new = copy.deepcopy(old)
        new["paths"]["/offer"]["get"]["parameters"].append({"name": "region", "in": "query", "type": "string", "required": True})
        self.assertEqual([c.rule for c in compare(old, new)], ["D003"])


class LoadAndCliTests(unittest.TestCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_rejects_non_openapi_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "x.json"
            bad.write_text('{"hello": 1}', encoding="utf-8")
            with self.assertRaises(SentinelError):
                load(bad)

    def test_rejects_broken_json_and_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "x.json"
            bad.write_text("{nope", encoding="utf-8")
            with self.assertRaises(SentinelError):
                load(bad)
        with self.assertRaises(SentinelError):
            load(FIX / "does-not-exist.json")

    def test_cli_exit_codes(self):
        self.assertEqual(self.run_cli("lint", str(FIX / "offer-api.json"))[0], 0)
        self.assertEqual(self.run_cli("lint", str(FIX / "offer-api-weak.json"))[0], 1)
        self.assertEqual(self.run_cli("lint", str(FIX / "offer-api-weak.json"), "--fail-on", "never")[0], 0)
        self.assertEqual(self.run_cli("diff", str(FIX / "offer-api-v1.json"), str(FIX / "offer-api-v2.json"))[0], 1)
        code, _, err = self.run_cli("lint", str(FIX / "missing.json"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)

    def test_cli_json_and_french(self):
        _, out, _ = self.run_cli("--format", "json", "--lang", "fr", "diff", str(FIX / "offer-api-v1.json"), str(FIX / "offer-api-v2.json"))
        data = json.loads(out)
        self.assertEqual(len(data), 7)
        self.assertIn("chemin supprimé", {d["message"] for d in data})


if __name__ == "__main__":
    unittest.main()
