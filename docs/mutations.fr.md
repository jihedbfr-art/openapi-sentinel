# Couverture des mutations

[English version](mutations.md)

Lancez `python -m unittest discover -s tests -p test_mutations.py` à la racine du dépôt. Le test utilise uniquement la bibliothèque standard et la graine `20261019`. Il produit 3 000 entrées mutées à partir des quatre fixtures JSON et appelle 9 000 fois le vrai point d'entrée CLI : lint, diff original-vers-muté et diff muté-vers-original. Le parseur, la lecture du disque, les contrôles et la sérialisation s'exécutent réellement. La découverte des extensions installées est isolée pour que les plugins locaux ne modifient pas le corpus.

Les neuf familles sont : suppression de clé ; remplacement par null, un nombre, une liste, un objet ou une chaîne ; duplication d'un élément de liste ; vidage d'un objet ; troncature du texte. Chaque fixture reçoit chaque famille. Le test alterne les sorties texte, JSON, Markdown et SARIF et les messages anglais/français. Chaque appel doit renvoyer 0, 1 ou 2 ; le code 2 exige stderr non vide et aucun flux ne doit contenir de traceback. Une exception inattendue fait échouer le test. L'ensemble des mutations doit finir en moins de 30 secondes.

Sous Windows avec Python 3.12.0, l'exécution contrôlée a duré 26,997 secondes : 5 710 appels ont renvoyé 0, 1 950 ont renvoyé 1 et 1 340 ont renvoyé 2. Aucune exception non gérée trouvée : il n'y a donc ni entrée minimale de plantage ni correction de plantage à annoncer.

Ce corpus reproductible reste borné et ne prouve pas la robustesse de toutes les entrées. Les appels restent dans le même processus au lieu de lancer 9 000 interpréteurs. Le dépôt ne contient aucune fixture YAML : seule la troncature JSON est couverte. Le parseur YAML, les extensions tierces, les profondeurs arbitraires et les services externes sont hors de ce test. La durée dépend de la machine ; l'assertion de 30 secondes reste active.

Les essais locaux antérieurs ont dépassé le budget ; son seuil n’a pas été changé. La CLI réutilise la définition du parseur et résout une URI une fois par source dans chaque rapport. Le SARIF est émis sans indentation, avec la même structure JSON. Le fichier temporaire reste ouvert en écriture, avec tampon vidé avant chaque vraie lecture CLI ; les bases sont des copies exactes des fixtures dans ce même répertoire temporaire. Aucun appel ni contrôle retiré.
