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

Options : `--lang en|fr`, `--format text|json|md`, et pour `lint` `--fail-on error|warn|never`. Codes de sortie : `0` rien à signaler, `1` constats (ou ruptures), `2` entrée illisible.

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
- `diff` compare les propriétés d'objets (y compris imbriquées), pas les variantes `oneOf` ni les valeurs d'énumération.

## Tests

```bash
python -m unittest discover -s tests
```

18 tests, bibliothèque standard uniquement. Les jeux d'essai sont des API inventées dans `fixtures/`.

## Étendre

Des fonctions de règles peuvent être ajoutées de l'extérieur par le groupe de points d'entrée `openapi_sentinel.rule_packs` ; voir [docs/extending.fr.md](docs/extending.fr.md).

## Licence et contact

Code : [Apache License 2.0](LICENSE). Des fonctions avancées peuvent être discutées sur demande : voir [COMMERCIAL.fr.md](COMMERCIAL.fr.md).

---

<p align="center">
  <img src="assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="80" height="80"><br>
  <sub>Conçu et maintenu sous <b>JihedAiLabs</b>.</sub>
</p>
