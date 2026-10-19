# Historique

[English version](CHANGELOG.md)

## 0.2.1

Ajout d'un contrôle de robustesse déterministe : 3 000 mutations des fixtures et 9 000 appels CLI couvrant lint, diff dans les deux sens, les quatre formats et les deux langues. Il supprime des clés, remplace des valeurs, duplique des éléments de liste, vide des objets et tronque le JSON ; il exige des erreurs lisibles sans traceback. Aucune exception non gérée trouvée dans ce corpus. Voir la [couverture des mutations](docs/mutations.fr.md).

Réutilisation du parseur CLI et des URI par rapport ; émission du SARIF sans indentation en conservant sa structure JSON.

## 0.2.0

Ajout de la sortie SARIF 2.1.0 pour lint et diff, avec messages traduits, descriptions de règles en anglais, URI de fichiers et localisations logiques. Les codes de sortie restent inchangés. Les deux README contiennent un exemple de téléversement à copier. 38 tests.

## 0.1.2

Corrections issues d'une revue indépendante, reproduites avant correction : diff compare les types scalaires, les éléments de tableaux, les types racines des réponses, les valeurs des dictionnaires (`additionalProperties`), chaque type de média, les schémas des paramètres OpenAPI 3, les opérations `trace`, les corps de requête devenus obligatoires et les champs imbriqués devenus obligatoires. L'ordre des branches `allOf` ne change plus les champs obligatoires. S003 compare les noms d'en-têtes sans tenir compte de la casse. Les `parameters`/`responses` mal formés produisent un message lisible et le code 2. `--lang fr` traduit aussi les libellés des rapports. 28 tests.

## 0.1.1

Diff compare désormais les propriétés imbriquées des objets et les éléments des réponses en tableau ; la version 0.1.0 ne comparait que les champs de premier niveau des objets seuls. Les nouvelles entrées obligatoires ne sont signalées que pour les champs de premier niveau du corps. 20 tests.

## 0.1.0

Première version publique : huit contrôles de conventions (lint), six contrôles de rupture (diff), messages en anglais et français, sorties texte/JSON/Markdown, point d'entrée pour les extensions de règles. 18 tests.
