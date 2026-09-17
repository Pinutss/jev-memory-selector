# jev-memory-selector

Sélection locale de souvenirs pour agents IA, avec classement explicable et budget configurable.

Projet de [JEV Labs](https://github.com/Pinutss/jev-labs).

## Statut

Prototype Python heuristique, sans appel réseau. L’intégration JEV n’est pas implémentée : sa documentation et son API restent à confirmer. Le protocole `Judge` est une proposition non raccordée au sélecteur, pas un adaptateur utilisable.

## Démarrer localement

Depuis le dossier `jev-memory-selector`, avec uv installé :

```bash
uv sync --extra dev
uv run pytest -q
uv run python examples/basic.py
uv build
```

## Comportement

- Filtrage par scope et expiration.
- Score lexical, fraîcheur à demi-vie configurable et importance.
- Sélection gloutonne dans le budget, sans tronquer les souvenirs.
- Déduplication approximative par recouvrement lexical.
- Raisons de sélection et de rejet disponibles dans le résultat.
- Compteur de tokens injectable, sans dépendance à un fournisseur.

## Exemple d’API

```python
from jev_memory_selector import HeuristicSelector, MemoryItem, SelectionRequest

result = HeuristicSelector().select(
    [MemoryItem(id="m1", text="Répondre en français", scope="alice")],
    SelectionRequest(query="français", scope="alice", budget_tokens=32),
)
print(result.texts)
```

## Limites importantes

Le compteur fourni estime un token pour quatre caractères. Le budget ne garantit donc que la somme de ces estimations, pas le nombre réel de tokens du modèle. Injecter son tokenizer et réserver séparément le coût du prompt, des séparateurs et des métadonnées.

Le classement est lexical, pas sémantique. Il peut retenir des souvenirs sans correspondance avec la requête ; la déduplication peut confondre des faits proches. Il ne résout pas les contradictions.

Le déterminisme du classement nécessite les mêmes données, la même horloge `now`, la même configuration et un compteur déterministe. Les IDs dupliqués sont traités dans l’ordre d’entrée ; l’ordre des rejets n’est pas canonique.

Le scope est un filtre, pas une authentification. L’appelant doit imposer les permissions et ne fournir que des données autorisées. Les rejets exposent des identifiants : ne pas retourner ce diagnostic à un utilisateur non autorisé. Le scope par défaut est partagé, utiliser un scope explicite en environnement multi-utilisateur.

Aucune persistance, protection contre l’injection de prompt, sandbox ou intégration JEV n’est fournie. Pas de benchmark comparatif ni de validation en production.

## Licence

À choisir avant distribution comme logiciel open source. Aucun paquet publié sur PyPI.
