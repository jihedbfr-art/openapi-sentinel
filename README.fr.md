<p align="center">
  <img src="assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="120" height="120">
</p>

# openapi-sentinel

[English version](README.md)

Vérifie une description OpenAPI/Swagger au regard des habitudes des API REST de type télécom, et liste les changements entre deux versions qui casseraient les appelants existants. Hors ligne, sans compte, sans dépendance, sans IA obligatoire.

> Projet indépendant. Sans affiliation, approbation ni certification de TM Forum ni d'aucun organisme de normalisation. Réussir ces contrôles ne dit rien de la conformité à une spécification.

## Pourquoi cet outil

Les descriptions publiques d'Open API télécom se ressemblent beaucoup : mêmes paramètres de pagination, mêmes en-têtes de comptage, entités qui portent `id`, `href` et `@type`, point `/hub` pour les notifications. Les équipes qui publient leurs propres API dans ce style s'en écartent sans le voir, et un champ renommé ou supprimé casse les consommateurs en silence. L'outil transforme ces habitudes en contrôles que l'on lance en une minute, et indique dans quels fichiers publics l'habitude a été observée ([docs/conventions.fr.md](docs/conventions.fr.md)).

## Démarrage rapide

Python 3.10 ou plus. Rien à installer pour l'essayer depuis un clone :

```bash
git clone https://github.com/jihedbfr-art/openapi-sentinel.git
cd openapi-sentinel
PYTHONPATH=src python -m openapi_sentinel --lang fr lint fixtures/offer-api-weak.json
PYTHONPATH=src python -m openapi_sentinel --lang fr diff fixtures/offer-api-v1.json fixtures/offer-api-v2.json
```

Ou installez-le (`pip install .`) et utilisez la commande `openapi-sentinel`. Le JSON fonctionne tel quel ; le YAML demande `pip install pyyaml`.

Options : `--lang en|fr` (messages et libellés du rapport ; `--help` reste en anglais), `--format text|json|md|sarif`, et pour `lint` `--fail-on error|warn|never` (défaut `error`). Codes de sortie : `lint` renvoie `0` quand aucun constat n'atteint le niveau `--fail-on` (des avertissements et infos peuvent quand même s'afficher) et `1` sinon ; `diff` renvoie `0` sans rupture et `1` sinon ; `2` signifie entrée illisible ou mal formée.

## Rapports SARIF

Placez `--format sarif` avant `lint` ou `diff` pour écrire du JSON SARIF 2.1.0 sur la sortie standard :

```bash
PYTHONPATH=src python -m openapi_sentinel --format sarif lint fixtures/offer-api-weak.json > results.sarif
PYTHONPATH=src python -m openapi_sentinel --lang fr --format sarif diff fixtures/offer-api-v1.json fixtures/offer-api-v2.json > changes.sarif
```

Le rapport contient les descriptions de toutes les règles internes en anglais et un résultat par constat, avec les messages dans la langue demandée. `error`, `warn` et `info` deviennent `error`, `warning` et `note` ; chaque résultat de diff porte le niveau `error`. Sans constat, le tableau `results` est vide. Les codes de sortie et `--fail-on` gardent leur sens actuel.

Les localisations contiennent une URI de fichier encodée et le chemin logique du constat, sans numéro de ligne inventé. Les fichiers dans le répertoire courant ont un chemin relatif ; les fichiers externes conservent une URI absolue. Lancez la commande à la racine du dépôt pour un téléversement portable. Les chemins, opérations, réponses et champs supprimés pointent vers l'ancien fichier ; les nouvelles obligations et les types modifiés vers le nouveau. Conservez les deux descriptions dans le checkout pour téléverser un diff. Les règles externes reçoivent une description générique en anglais et gardent leurs propres messages de résultat.

Voici un **fragment de job à copier**, pas un workflow installé. Il suppose Python 3.10+ et l'organisation des sources de ce dépôt ; adaptez le chemin d'entrée. Le téléversement reste exécuté après des constats (code 1), mais le contrôle reste en échec. Une erreur d'entrée (code 2) fait échouer le contrôle et empêche le téléversement. Pour un diff, utilisez la commande diff et une catégorie distincte comme `openapi-sentinel-diff`.

```yaml
permissions:
  contents: read
  security-events: write
steps:
  - uses: actions/checkout@v6
  - name: Check API
    id: sentinel
    shell: bash
    run: |
      status=0
      PYTHONPATH=src python -m openapi_sentinel --format sarif lint fixtures/offer-api-weak.json > results.sarif || status=$?
      echo "status=$status" >> "$GITHUB_OUTPUT"
      exit "$status"
  - name: Upload SARIF
    if: ${{ !cancelled() && (steps.sentinel.outputs.status == '0' || steps.sentinel.outputs.status == '1') }}
    uses: github/codeql-action/upload-sarif@v4
    with:
      sarif_file: results.sarif
      category: openapi-sentinel-lint
```

GitHub décrit l'action et les permissions requises dans [Téléverser un fichier SARIF](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/integrate-with-existing-tools/upload-sarif-file) (consulté le 18 octobre 2026). La sortie suit le [schéma OASIS SARIF 2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/schemas/sarif-schema-2.1.0.json) (consulté le 18 octobre 2026). La validation locale du schéma ne confirme pas l'acceptation par un service hébergé d'analyse de code ; aucun téléversement réel n'a été effectué pour ce changement.

## Ce qui est contrôlé

| Règle | Niveau | Contrôle |
|---|---|---|
| S001 | erreur/avert. | chaque opération a un `operationId` unique |
| S002 | avert. | le `GET` de collection accepte `fields`, `offset`, `limit` |
| S003 | avert. | le 200 du `GET` de collection déclare `X-Total-Count` et `X-Result-Count` |
| S004 | avert. | les schémas avec un `href` ont aussi `id` et `@type` (les charges de notification se terminant par `Event` sont ignorées) |
| S005 | avert. | chaque opération déclare 400 et 500, plus 404 sur les chemins avec identifiant |
| S006 | info | un point d'inscription `POST /hub` existe |
| S007 | avert. | `info.version` est présent |
| S008 | info | chaque opération a un résumé ou une description |

`diff` signale : chemin supprimé (D001), opération supprimée (D002), nouvelle entrée obligatoire (D003), réponse de succès supprimée (D004), champ de réponse supprimé (D005), type de champ modifié (D006). Les ajouts ne sont pas signalés.

## Limites

- Contrôles statiques du fichier de description uniquement. Rien n'est appelé : le comportement d'un service en marche n'est pas testé.
- Swagger 2.0 et OpenAPI 3.x sont lus ; seules les références `$ref` locales sont suivies.
- Les conventions sont des observations sur cinq fichiers publics, résumées dans [docs/conventions.fr.md](docs/conventions.fr.md). C'est un point de départ, pas une norme. Sur ces cinq mêmes fichiers, l'outil signale cinq schémas (`Addressable` deux fois, `EntityValue`, `Place`, `Service`) qui portent un `href` sans `@type`, et rien d'autre.
- `diff` compare les propriétés d'objets (y compris imbriquées), pas les variantes `oneOf`/`anyOf` ni les valeurs d'énumération, et ne signale ni un champ devenu facultatif ni un format plus étroit. Un champ retiré d'un corps de requête n'est pas signalé, bien qu'un serveur strict puisse rejeter les appelants qui l'envoient encore.

## Tests

```bash
python -m unittest discover -s tests
```

38 tests, bibliothèque standard uniquement. Les jeux d'essai sont des API inventées dans `fixtures/`.

## Étendre

Des fonctions de règles peuvent être ajoutées de l'extérieur par le groupe de points d'entrée `openapi_sentinel.rule_packs` ; voir [docs/extending.fr.md](docs/extending.fr.md).

## Parcours d'étude

Les idées derrière ces contrôles sont expliquées, avec sources et exercices, dans le parcours d'étude bilingue [oda-learning-lab](https://github.com/jihedbfr-art/oda-learning-lab/blob/main/docs/fr/04-les-open-apis-en-pratique.md) (module 4).

## Licence et contact

Code : [Apache License 2.0](LICENSE). Des fonctions avancées peuvent être discutées sur demande : voir [COMMERCIAL.fr.md](COMMERCIAL.fr.md).

---

<p align="center">
  <img src="assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="80" height="80"><br>
  <sub>Conçu et maintenu sous <b>JihedAiLabs</b>.</sub>
</p>
