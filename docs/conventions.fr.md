# Conventions derrière les contrôles

[English version](conventions.md)

Les règles d'`openapi-sentinel` viennent de la lecture de cinq descriptions Open API publiques, figées à des commits précis pour que chacun puisse refaire l'observation. Lues le 2026-10-16. Ce sont des habitudes vues dans ces fichiers, pas un jeu de règles officiel, et rien ici ne reproduit un schéma ni une charge utile d'exemple.

## Les cinq fichiers

| API | Fichier (commit figé) | Licence du dépôt |
|---|---|---|
| Product Catalog Management 4.1.0 | [TMF620](https://github.com/tmforum-apis/TMF620_ProductCatalog/blob/24e69f3026f2b514baa27d7206540fc7b55bcb45/TMF620-ProductCatalog-v4.1.0.swagger.json) | Apache-2.0, [LICENSE](https://github.com/tmforum-apis/TMF620_ProductCatalog/blob/24e69f3026f2b514baa27d7206540fc7b55bcb45/LICENSE) |
| Product Ordering 4.0.0 | [TMF622](https://github.com/tmforum-apis/TMF622_ProductOrder/blob/a3825f95248eb04fb1c7e2321305bc99631168a4/TMF622-ProductOrder-v4.0.0.swagger.json) | Apache-2.0, [LICENSE](https://github.com/tmforum-apis/TMF622_ProductOrder/blob/a3825f95248eb04fb1c7e2321305bc99631168a4/LICENSE) |
| Service Inventory Management 4.0.0 | [TMF638](https://github.com/tmforum-apis/TMF638_ServiceInventory/blob/50fc82942e423c81896362d1ab9847f7c918cf7f/TMF638-ServiceInventory-v4.0.0.swagger.json) | Apache-2.0, [LICENSE](https://github.com/tmforum-apis/TMF638_ServiceInventory/blob/50fc82942e423c81896362d1ab9847f7c918cf7f/LICENSE) |
| Product Inventory 4.0.0 | [TMF637](https://github.com/tmforum-apis/TMF637_ProductInventory/blob/f598b4a02186071f2794b8f9b4f6904ef0a8aa52/TMF637-ProductInventory-v4.0.0.swagger.json) | Apache-2.0, [LICENSE](https://github.com/tmforum-apis/TMF637_ProductInventory/blob/f598b4a02186071f2794b8f9b4f6904ef0a8aa52/LICENSE) |
| Resource Inventory Management 4.0.0 | [TMF639](https://github.com/tmforum-apis/TMF639_ResourceInventory/blob/2693a854940de3c6e15b1aade24f981d94b75d3a/TMF639-ResourceInventory-v4.0.0.swagger.json) | Apache-2.0, [LICENSE](https://github.com/tmforum-apis/TMF639_ResourceInventory/blob/2693a854940de3c6e15b1aade24f981d94b75d3a/LICENSE) |

Les cinq sont des fichiers Swagger 2.0. La mention de licence vaut pour ces dépôts seulement. Ce projet ne copie aucun de leurs contenus ; il en lit la structure.

## Ce qui a été observé, et la règle qui en découle

| Observation (les cinq fichiers) | Règle |
|---|---|
| Chaque opération a un `operationId` | S001 |
| Chaque `GET` de collection a les paramètres `fields`, `offset` et `limit` | S002 |
| Chaque 200 de `GET` de collection déclare `X-Total-Count` et `X-Result-Count` | S003 |
| Les schémas d'entité qui portent un `href` portent aussi `id`, et presque tous `@type` | S004 |
| Les opérations déclarent les réponses 400, 401, 403, 404, 405, 409 et 500 ; l'outil n'exige que 400 et 500 (404 sur les chemins avec identifiant) | S005 |
| Un chemin `/hub` avec une opération d'inscription, et des chemins `/listener/...` pour les événements | S006 (les chemins listener ne sont pas contrôlés) |
| `info.version` est renseigné | S007 |

Les schémas de charge d'événement (noms finissant par `Event`) ne suivent pas le motif d'entité dans ces fichiers, donc S004 les ignore. Lancé sur les cinq fichiers, l'outil renvoie cinq avertissements S004 (`Addressable` dans deux fichiers, `EntityValue`, `Place`, `Service`) et rien d'autre : les règles sont aussi strictes que les fichiers eux-mêmes, pas plus.

## Ce que cela n'établit pas

Une règle réussie ne montre pas la conformité à une spécification, et une règle en échec ne montre pas qu'une API a tort. Les versions plus récentes de ces API peuvent différer. Consultez la publication officielle pour ce qui s'applique à votre cas.
