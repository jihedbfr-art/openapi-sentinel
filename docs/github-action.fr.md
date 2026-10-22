# Action GitHub

[English version](github-action.md)

Exécuter le lint ou comparer deux descriptions OpenAPI dans une pull request. L’Action produit un rapport SARIF et conserve les codes de sortie de la CLI : une rupture fait échouer l’étape.

## Exemple de lint

Adapter `api/openapi.yaml` au fichier du projet. Cet exemple référence un commit précis de l’implémentation fusionnée ; il ne suppose ni tag `v1` ni publication Marketplace.

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

L’étape de conservation du rapport peut s’exécuter après un constat sans rendre le contrôle vert. Elle conserve un artefact téléchargeable ; elle ne crée pas d’annotation dans la PR et ne téléverse rien vers Code Scanning.

## Exemple de diff

Les deux descriptions doivent être présentes dans le checkout. L’Action ne récupère aucune branche de base à votre place.

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

## Entrées et sorties

| Entrée | Défaut | Usage |
|---|---|---|
| `mode` | `lint` | `lint` ou `diff` |
| `spec` | obligatoire | Description à vérifier ; nouvelle version en mode diff |
| `baseline` | vide | Ancienne version, obligatoire pour diff |
| `lang` | `en` | `en` ou `fr` pour les messages du rapport |
| `fail-on` | `error` | `error`, `warn` ou `never` pour lint ; ignoré par diff |
| `report` | `openapi-sentinel.sarif` | Chemin de sortie dans le workspace, suffixe `.sarif` |

Entrées et rapport sont résolus par rapport au workspace du dépôt appelant et doivent y rester, y compris après résolution des liens symboliques. Les chemins avec espaces ou caractères shell sont traités comme des chemins. Le rapport ne peut pas écraser un fichier d’entrée. Donner un nom différent à chaque invocation.

Sorties : `exit-code`, `sarif-file` et `findings`. Le nombre de résultats inclut ceux sous le seuil d’échec. Le code 0 signifie que le contrôle réussit, pas nécessairement qu’il ne trouve rien ; `fail-on: never` laisse toujours passer les constats de lint. Le code 1 signale un seuil atteint ou une rupture ; le code 2, une entrée ou une exécution invalide.

`sarif-file` et `findings` sont produits seulement lorsqu’un rapport valide a été généré avec le code 0 ou 1. Une erreur ne supprime pas un ancien fichier déjà présent au même emplacement : utiliser les sorties de l’étape courante pour décider d’un téléversement. Un échec de configuration Python ou d’installation peut survenir avant que les sorties existent.

## Environnement et limites

L’Action sélectionne Python 3.12 puis crée un environnement virtuel temporaire propre à chaque invocation. Elle y installe le code de la révision de l’Action et l’option YAML. Le réseau est nécessaire à cette installation ; les contrôles de descriptions fonctionnent ensuite localement. Aucun secret ni permission d’écriture GitHub n’est requis. L’environnement temporaire reste dans le dossier temporaire du runner jusqu’à son nettoyage normal.

La CI de cette proposition exerce l’Action sur les runners GitHub Ubuntu et Windows, avec un répertoire d’Action distinct des fichiers du projet appelant. Les autres runners et l’acceptation par GitHub Code Scanning ne sont pas couverts. Pour un téléversement Code Scanning ultérieur, configurer séparément la permission et l’action d’envoi selon les instructions SARIF du README.

Les conventions du linter et les limites du diff restent celles de la CLI. Il ne contacte pas l’API décrite et ne certifie aucune conformité à un standard. Les dépendances de build et PyYAML ne sont pas verrouillées ; le commit de l’Action est fixe, pas l’ensemble transitif des installations.

Références : [actions composites](https://docs.github.com/en/actions/tutorials/create-actions/create-a-composite-action), [sécurité des entrées](https://docs.github.com/en/actions/reference/security/secure-use).

---

<div align="center">
  <img src="../assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="120"/>
  <br/>
  <sub>Un projet <a href="https://github.com/jihedbfr-art"><b>JihedAiLabs</b></a></sub>
</div>
