# GitHub Action

[Version française](github-action.fr.md)

Run lint or compare two OpenAPI descriptions in a pull request. The action writes SARIF and preserves the CLI exit codes: a breaking change fails the step.

## Lint example

Replace `api/openapi.yaml` with your project's file. This example pins a specific commit of the merged implementation; it assumes neither a `v1` tag nor a Marketplace listing.

```yaml
name: Check API
on: pull_request
permissions:
  contents: read
jobs:
  api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check description
        id: sentinel
        uses: jihedbfr-art/openapi-sentinel@cdef50117cae0396ef48dd0c4be6af796d303010
        with:
          spec: api/openapi.yaml
          fail-on: warn
      - name: Retain SARIF
        if: ${{ !cancelled() && (steps.sentinel.outputs.exit-code == '0' || steps.sentinel.outputs.exit-code == '1') }}
        uses: actions/upload-artifact@v4
        with:
          name: openapi-sentinel
          path: ${{ steps.sentinel.outputs.sarif-file }}
```

The report retention step can run after findings without making the check green. It saves a downloadable artifact; it neither annotates the PR nor uploads to Code Scanning.

## Diff example

Both descriptions must be present in the checkout. The action does not fetch a base branch for you.

```yaml
- name: Detect breaking changes
  id: sentinel
  uses: jihedbfr-art/openapi-sentinel@cdef50117cae0396ef48dd0c4be6af796d303010
  with:
    mode: diff
    baseline: api/old.yaml
    spec: api/new.yaml
    lang: fr
    report: reports/breaking.sarif
```

## Inputs and outputs

| Input | Default | Purpose |
|---|---|---|
| `mode` | `lint` | `lint` or `diff` |
| `spec` | required | Description to check; new version for diff |
| `baseline` | empty | Old version, required for diff |
| `lang` | `en` | `en` or `fr` for report messages |
| `fail-on` | `error` | `error`, `warn` or `never` for lint; ignored for diff |
| `report` | `openapi-sentinel.sarif` | Output path inside the workspace, ending in `.sarif` |

Inputs and reports resolve against the caller repository's workspace and must remain inside it, including after symlink resolution. Paths with spaces or shell characters remain literal paths. The report cannot overwrite an input file. Use a distinct report name for each invocation.

Outputs are `exit-code`, `sarif-file` and `findings`. The finding count includes results below the failure threshold. Exit 0 means the check passes, not necessarily that there are no findings; `fail-on: never` always passes lint findings. Exit 1 means a threshold was reached or a breaking change was found; exit 2 means invalid input or execution.

`sarif-file` and `findings` exist only when a valid report was generated with exit 0 or 1. An error does not delete an older file already at the same path: use the current step outputs to decide whether to upload. Python setup or installation failures may occur before any outputs exist.

## Environment and limits

The action selects Python 3.12, then creates a separate temporary virtual environment for each invocation. It installs the code from the action revision and its YAML extra there. Installation needs network access; description checks then run locally. No secret or GitHub write permission is required. The temporary environment stays in the runner's temporary directory until normal runner cleanup.

This proposal's CI exercises the action on GitHub Ubuntu and Windows runners, with the action directory separate from the caller's inputs. Other runners and GitHub Code Scanning acceptance are not covered. For a later Code Scanning upload, configure the upload action and permission separately, following the README's SARIF instructions.

Linter conventions and diff limits remain those of the CLI. It does not call the described API or certify conformance to a standard. Build dependencies and PyYAML are not locked; the action commit is pinned, not the complete transitive installation.

References: [composite actions](https://docs.github.com/en/actions/tutorials/create-actions/create-a-composite-action), [input security](https://docs.github.com/en/actions/reference/security/secure-use).

---

<div align="center">
  <img src="../assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="120"/>
  <br/>
  <sub>A <a href="https://github.com/jihedbfr-art"><b>JihedAiLabs</b></a> project</sub>
</div>
