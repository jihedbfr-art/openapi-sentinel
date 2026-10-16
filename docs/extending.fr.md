# Ajouter des règles de l'extérieur

[English version](extending.md)

`openapi-sentinel lint` charge des fonctions de règles depuis tout paquet installé qui déclare un point d'entrée dans le groupe `openapi_sentinel.rule_packs`. Le point d'entrée doit pointer vers une liste (ou un tuple) de fonctions.

Une fonction de règle reçoit la description chargée (un `dict`) et renvoie une liste de `openapi_sentinel.rules.Finding` :

```python
from openapi_sentinel.rules import Finding, WARN

def no_trailing_slash(doc):
    return [Finding("X001", WARN, path, (("message", "le chemin finit par une barre oblique"),))
            for path in doc["paths"] if path.endswith("/") and path != "/"]

RULES = [no_trailing_slash]
```

```toml
# pyproject.toml de votre propre paquet
[project.entry-points."openapi_sentinel.rule_packs"]
mypack = "mypack:RULES"
```

Le noyau ne traduit que ses propres identifiants (`S001` à `S008`) ; un constat personnalisé fournit son texte par le paramètre `message`, comme ci-dessus. Un paquet qui échoue à l'import est ignoré avec un avertissement et le résultat du noyau est tout de même affiché.

Les paquets s'exécutent avec vos droits. N'installez que du code de confiance.
