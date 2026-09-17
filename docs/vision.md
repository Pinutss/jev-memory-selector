# VISION : document de produit, pas le contrat d'API

Ce fichier décrit la cible à long terme. L'API et le comportement réels
sont ceux du README et du package `jev-memory-selector` 0.2.x.

---

# 🧠 JEV Memory Selector

> **Intelligent context selection for AI agents.**
>
> Give it a query and a memory pool. It decides which memories are actually worth sending to your agent.

---

# 1. 🎯 Le problème

Aujourd'hui, beaucoup d'agents font quelque chose comme :

```text
Utilisateur
     ↓
Question
     ↓
Vector DB
     ↓
Top 10 similar memories
     ↓
LLM
```

Le problème est que :

**similarité ≠ utilité**

Exemple :

```text
Memory 1:
"Le projet utilise React."

Memory 2:
"Le projet utilise React avec TypeScript."

Memory 3:
"Le projet actuel utilise Next.js."

Memory 4:
"Le projet précédent utilisait React."

Memory 5:
"Le serveur tourne sous Debian."
```

L'utilisateur demande :

> « Comment est configuré mon projet actuel ? »

Une recherche vectorielle peut retourner les cinq.

Mais le selector devrait comprendre :

```text
Memory 3 → HIGH
Memory 5 → MEDIUM
Memory 1 → LOW
Memory 2 → LOW
Memory 4 → IGNORE
```

---

# 2. 💡 Ce que fait JEV Memory Selector

Le projet ajoute une couche entre :

```text
Memory Storage
      ↓
Retrieval
      ↓
┌────────────────────┐
│ JEV Memory Selector│
└──────────┬─────────┘
           ↓
Relevant memories
           ↓
Agent / LLM
```

Son rôle est uniquement de répondre à :

> **« Parmi toutes ces informations, lesquelles dois-je donner à l'agent maintenant ? »**

Il ne doit **pas être responsable de la génération de texte**.

---

# 3. 🏗️ Architecture générale

```text
                    ┌─────────────────────┐
                    │       AI Agent      │
                    └──────────┬──────────┘
                               │
                            Query
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Memory Selector   │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
             Memory Retriever       Current Context
                    │
                    ▼
             Candidate Memories
                    │
                    ▼
                   JEV
                    │
                    ▼
          Relevance / Selection
                    │
                    ▼
             Selected Memories
                    │
                    ▼
                    Agent
```

---

# 4. 🔥 Principe fondamental

**JEV ne doit pas remplacer la mémoire.**

Il doit être une couche de décision.

Donc :

```text
Memory
  ↓
Retriever
  ↓
JEV
  ↓
Context
```

et non :

```text
JEV
 ↓
Database
 ↓
Everything
```

Cela rend le projet compatible avec pratiquement n'importe quelle architecture.

---

# 5. 🌍 Compatibilité universelle

Le projet doit fonctionner avec :

## Agents

- OpenAI Agents
- Claude
- Claude Code
- Gemini
- Codex
- Cursor
- Windsurf
- OpenClaw
- Hermes
- LangChain
- LangGraph
- CrewAI
- AutoGen
- LlamaIndex
- agents custom

## Stockage

- SQLite
- PostgreSQL
- Redis
- MongoDB
- fichiers JSON
- Markdown
- fichiers YAML
- vector databases
- Pinecone
- Qdrant
- Weaviate
- Chroma
- Supabase
- mémoire en RAM

## Embeddings

- OpenAI
- Gemini
- Voyage
- Cohere
- modèles locaux
- Ollama
- sentence-transformers

## LLM

Et surtout :

**aucun LLM ne doit être obligatoire.**

---

# 6. 🔑 Quelle API Key ?

C'est un point essentiel.

## JEV doit être la seule API nécessaire au selector

Pour le mode cloud :

```env
JEV_API_KEY=jev_xxxxxxxxx
```

Le projet **ne doit pas demander** :

```env
OPENAI_API_KEY
ANTHROPIC_API_KEY
GEMINI_API_KEY
```

pour fonctionner avec le provider JEV.

---

# 7. 🧠 Mode local

Pour rendre le projet réellement universel, prévoir également un mode 100 % local :

```text
                 JEV Memory Selector
                         │
             ┌───────────┴───────────┐
             │                       │
          Cloud                    Local
             │                       │
         JEV API              Local decision model
```

### Mode 1 : JEV Cloud

```env
JEV_PROVIDER=jev
JEV_API_KEY=...
```

### Mode 2 : Local

```env
JEV_PROVIDER=local
```

Aucune API distante obligatoire.

### Mode 3 : Custom endpoint

```env
JEV_PROVIDER=custom
JEV_BASE_URL=http://localhost:8000
```

Cela permet aux utilisateurs de brancher leur propre implémentation compatible.

---

# 8. ⚠️ Ne pas imposer d'embeddings

Le selector doit pouvoir recevoir directement :

```json
{
  "id": "memory_123",
  "content": "Le projet utilise PostgreSQL"
}
```

sans embedding.

Mais il doit également pouvoir recevoir :

```json
{
  "id": "memory_123",
  "content": "Le projet utilise PostgreSQL",
  "similarity": 0.91
}
```

Donc :

```text
Retriever
   ↓
Candidates
   ↓
JEV
```

Le retriever est interchangeable.

---

# 9. 📦 API idéale

Python :

```python
from jev_memory_selector import MemorySelector

selector = MemorySelector(
    provider="jev",
    api_key="jev_..."
)

result = selector.select(
    query="Comment fonctionne mon backend ?",
    memories=memories,
    budget=5
)
```

Résultat :

```python
{
    "selected": [
        {
            "id": "memory_42",
            "score": 0.96,
            "reason": "Directly related to backend architecture"
        },
        {
            "id": "memory_17",
            "score": 0.82
        }
    ]
}
```

---

# 10. 🧩 API universelle

Pour les utilisateurs qui ont déjà leur propre système :

```python
selector = MemorySelector(
    provider="jev"
)

result = selector.select(
    query=query,
    candidates=retrieved_memories
)
```

Le selector **ne sait même pas où les memories sont stockées**.

---

# 11. 📐 Schéma des données

Une memory devrait avoir au minimum :

```json
{
  "id": "mem_123",
  "content": "The project uses PostgreSQL",
  "metadata": {
    "source": "conversation",
    "created_at": "2026-09-17T12:00:00Z",
    "project": "my-project"
  }
}
```

Optionnel :

```json
{
  "embedding": [...],
  "similarity": 0.87,
  "importance": 0.8,
  "timestamp": "...",
  "namespace": "project-a"
}
```

---

# 12. 🧠 Ce que JEV doit décider

Pour chaque mémoire :

```text
RELEVANT ?
    ↓
YES / NO

IMPORTANCE ?
    ↓
0 → 1

CURRENT ?
    ↓
YES / NO

USEFUL ?
    ↓
YES / NO
```

Recommandation : garder une sortie principale simple :

```json
{
  "selected": true,
  "confidence": 0.94
}
```

Puis éventuellement :

```json
{
  "selected": true,
  "confidence": 0.94,
  "priority": 0.87
}
```

---

# 13. 🚀 Traitement par batch

Ne pas faire :

```text
Memory 1 → JEV
Memory 2 → JEV
Memory 3 → JEV
Memory 4 → JEV
...
```

Mais :

```text
                    JEV
                     │
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
    Memory 1      Memory 2      Memory 3
       ↓             ↓             ↓
     score          score         score
```

L'objectif est d'évaluer les candidats efficacement dans une même opération lorsque le provider le permet.

---

# 14. 📊 Pipeline complet

```text
USER QUERY
    │
    ▼
┌───────────────┐
│ Query Analyzer│
└───────┬───────┘
        │
        ▼
┌────────────────┐
│ Memory Adapter │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Candidate Pool │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ JEV Selector   │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Rank / Filter  │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Token Budget   │
└───────┬────────┘
        │
        ▼
   FINAL CONTEXT
        │
        ▼
       AGENT
```

---

# 15. 💰 Token Budget

Une fonctionnalité essentielle.

Exemple :

```python
selector.select(
    query=query,
    memories=memories,
    max_memories=8,
    max_tokens=3000
)
```

Le système doit choisir les informations pertinentes tout en respectant :

```text
TOTAL <= 3000 tokens
```

Exemple :

```text
Memory A = 500 tokens
Memory B = 400
Memory C = 300
Memory D = 1200
Memory E = 900
```

Le selector doit optimiser la sélection en fonction du budget.

---

# 16. 🧮 Scoring hybride

JEV ne doit pas être le seul signal.

On peut calculer :

```text
Final Score =
    JEV relevance
    ×
    Retrieval similarity
    ×
    Recency
    ×
    Importance
```

Exemple configurable :

```yaml
scoring:
  jev: 0.40
  similarity: 0.30
  recency: 0.15
  importance: 0.15
```

Les poids doivent être configurables par l'utilisateur.

---

# 17. 🔄 Gestion des souvenirs contradictoires

Fonctionnalité importante.

Exemple :

```text
Memory 1:
"Le projet utilise MySQL."

Memory 2:
"Le projet utilise PostgreSQL."

Memory 3:
"Migration vers PostgreSQL terminée."
```

Le selector peut identifier :

```text
Memory 1 → outdated
Memory 2 → relevant
Memory 3 → highly relevant
```

L'objectif est de privilégier l'état actuel plutôt que la simple similarité.

---

# 18. 🔒 Privacy by design

Le projet doit éviter de devenir un aspirateur à données.

### Par défaut

Ne jamais envoyer :

```text
API keys
passwords
tokens
private keys
cookies
credentials
```

avant JEV.

Pipeline :

```text
Memory
 ↓
Secret Detector
 ↓
Redaction
 ↓
JEV
```

Exemple :

```text
sk-ant-api03-xxxxxxxx
```

devient :

```text
[REDACTED_API_KEY]
```

---

# 19. 🔐 Gestion des API keys

Le projet lui-même ne doit jamais stocker les clés.

Support :

```env
JEV_API_KEY=
```

ou :

```python
MemorySelector(
    api_key=os.environ["JEV_API_KEY"]
)
```

Ne jamais faire :

```text
❌ clé dans config.json
❌ clé dans memory
❌ clé dans logs
❌ clé dans Git
❌ clé envoyée au LLM
```

---

# 20. 🧩 Architecture des providers

Créer une interface commune :

```python
class DecisionProvider:

    def select(
        self,
        query,
        memories
    ):
        raise NotImplementedError
```

Puis :

```text
providers/
├── jev.py
├── local.py
├── mock.py
└── custom.py
```

Utilisation :

```python
MemorySelector(provider="jev")
```

ou :

```python
MemorySelector(provider="local")
```

ou :

```python
MemorySelector(provider="custom")
```

---

# 21. 🌐 REST API

Fournir également une API HTTP.

```http
POST /v1/select
```

### Request

```json
{
  "query": "How does the backend work?",
  "memories": [
    {
      "id": "1",
      "content": "Backend uses FastAPI"
    },
    {
      "id": "2",
      "content": "Frontend uses React"
    }
  ],
  "max_memories": 5
}
```

### Response

```json
{
  "selected": [
    {
      "id": "1",
      "confidence": 0.97
    }
  ]
}
```

---

# 22. 🔌 MCP

Ajouter un serveur MCP pour que le système soit utilisable directement depuis les agents compatibles.

```text
Claude
Cursor
Codex
Gemini
OpenClaw
Hermes
      │
      ▼
    MCP
      │
      ▼
JEV Memory Selector
```

Tools :

```text
memory_select
memory_recall
memory_context
memory_stats
```

---

# 23. 🧰 Exemple MCP

L'agent pourrait appeler :

```json
{
  "query": "What database does this project use?",
  "limit": 5
}
```

Et recevoir :

```json
{
  "memories": [
    {
      "content": "Production uses PostgreSQL 16.",
      "confidence": 0.98
    }
  ]
}
```

---

# 24. 📁 Structure GitHub

```text
jev-memory-selector/
│
├── src/
│   └── jev_memory_selector/
│       ├── core/
│       ├── providers/
│       │   ├── jev.py
│       │   ├── local.py
│       │   └── mock.py
│       │
│       ├── retrievers/
│       │   ├── base.py
│       │   ├── vector.py
│       │   └── keyword.py
│       │
│       ├── security/
│       │   ├── redaction.py
│       │   └── secrets.py
│       │
│       ├── scoring/
│       ├── adapters/
│       └── api/
│
├── mcp/
│
├── examples/
│   ├── openai/
│   ├── claude/
│   ├── langchain/
│   ├── langgraph/
│   ├── cursor/
│   ├── codex/
│   ├── hermes/
│   └── custom-agent/
│
├── tests/
│
├── benchmarks/
│
├── docs/
│
├── docker/
│
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── LICENSE
└── README.md
```

---

# 25. 🐳 Docker

Quelqu'un doit pouvoir faire :

```bash
git clone ...
cd jev-memory-selector

cp .env.example .env

docker compose up
```

Et obtenir le service localement, par exemple :

```text
localhost:8080
```

---

# 26. 🧪 Mode Demo sans API

Très important pour GitHub.

Quelqu'un doit pouvoir faire :

```bash
pip install jev-memory-selector

jev-memory demo
```

sans aucune API.

On utilise alors :

```text
Mock Provider
```

Cela permet de tester l'architecture immédiatement.

---

# 27. 📊 Benchmark

Le repo doit fournir des datasets :

```text
benchmarks/
├── coding.json
├── personal_assistant.json
├── customer_support.json
├── devops.json
├── research.json
└── mixed.json
```

Puis :

```bash
jev-memory benchmark
```

Résultat possible :

```text
Memory Selector Benchmark

Candidates:       1000
Selected:            12

Precision:         94.2%
Recall:            91.7%
Tokens saved:      78.4%
Latency:           183ms
Cost:              provider-dependent
```

Les chiffres ci-dessus sont des exemples d'affichage, pas des performances garanties.

---

# 28. 🔥 Killer feature : `context_budget`

Une fonctionnalité centrale.

Exemple :

```python
selector.context(
    query=query,
    memories=memories,
    budget=2000
)
```

Le système comprend :

> « J'ai seulement 2 000 tokens disponibles. »

et choisit automatiquement les informations maximisant leur utilité.

```text
100 memories
      ↓
JEV
      ↓
42 candidates
      ↓
ranking
      ↓
12 memories
      ↓
2,000 token budget
      ↓
7 memories
      ↓
Agent
```

---

# 29. 🏆 Positionnement du projet

Ne pas le présenter comme :

> « Une base de mémoire pour agents IA. »

Mais comme :

> **JEV Memory Selector : an intelligent context layer for AI agents.**

Pitch :

> **Your agent doesn't need more memory. It needs better memory selection.**

L'idée centrale est que JEV serve de couche de décision entre la mémoire/récupération et le contexte réellement transmis à l'agent.

---

# 30. 🔑 Configuration finale

Le `.env.example` peut rester extrêmement simple :

```env
# JEV
JEV_API_KEY=

# Provider
JEV_PROVIDER=jev

# Optional
JEV_MODEL=jev-latest
JEV_BASE_URL=

# Selector
JEV_MEMORY_MAX_CANDIDATES=50
JEV_MEMORY_MAX_RESULTS=10
JEV_MEMORY_MAX_TOKENS=4000

# Security
JEV_REDACT_SECRETS=true

# Server
JEV_MEMORY_HOST=127.0.0.1
JEV_MEMORY_PORT=8080
```

Pour le mode JEV Cloud, `JEV_API_KEY` est la clé que l'application expose à l'utilisateur. L'implémentation du provider doit encapsuler les détails d'authentification propres au SDK/service JEV afin de ne pas coupler toute la librairie à un nom de variable ou à un fournisseur précis.

---

# 31. 🌍 Architecture finale

```text
                    ANY AGENT
                        │
        ┌───────────────┼────────────────┐
        │               │                │
      Claude          Codex           Cursor
        │               │                │
        └───────────────┼────────────────┘
                        │
                       MCP
                        │
                        ▼
             ┌────────────────────┐
             │ JEV MEMORY SELECTOR│
             └─────────┬──────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
       SQLite       Qdrant       Redis
          │            │            │
          └────────────┼────────────┘
                       │
                  Candidates
                       │
                       ▼
                      JEV
                       │
              ┌────────┴────────┐
              │                 │
          Relevant          Irrelevant
              │                 │
              ▼                 ✕
        Token Budget
              │
              ▼
        Optimized Context
              │
              ▼
             AGENT
```

---

# 32. 🚀 Vision

L'utilisateur ne devrait jamais avoir à changer son stack.

Il garde :

- sa DB
- son agent
- son vector store
- son LLM
- ses embeddings
- son framework

`jev-memory-selector` vient simplement s'intercaler entre :

> **« J'ai récupéré beaucoup de contexte »**

et :

> **« Voilà le contexte que mon agent doit réellement voir. »**

La philosophie du projet :

```text
ANY MEMORY
     +
ANY RETRIEVER
     +
ANY AGENT
     +
ANY LLM
     +
ANY STACK
     ↓
JEV MEMORY SELECTOR
     ↓
BETTER CONTEXT
```

---

# 33. 🛠️ Roadmap proposée

## Phase 1 : Core

- [ ] Python package
- [ ] Memory schema
- [ ] Provider abstraction
- [ ] JEV provider
- [ ] Mock provider
- [ ] Basic selection
- [ ] Tests unitaires

## Phase 2 : Context

- [ ] Ranking
- [ ] Token budget
- [ ] Recency
- [ ] Importance
- [ ] Duplicate detection
- [ ] Contradiction detection

## Phase 3 : Integrations

- [ ] REST API
- [ ] MCP server
- [ ] Qdrant
- [ ] PostgreSQL
- [ ] Redis
- [ ] SQLite
- [ ] LangChain
- [ ] LangGraph

## Phase 4 : Security

- [ ] Secret detection
- [ ] Redaction
- [ ] Audit logs
- [ ] Privacy controls
- [ ] Local-only mode

## Phase 5 : Evaluation

- [ ] Benchmark datasets
- [ ] Precision / recall
- [ ] Token savings
- [ ] Latency
- [ ] Cost tracking
- [ ] Regression tests

## Phase 6 : Developer Experience

- [ ] CLI
- [ ] Docker
- [ ] Documentation
- [ ] Examples
- [ ] Web demo
- [ ] GitHub Actions
- [ ] PyPI package

---

# 34. 🎯 Objectif final

Faire de `jev-memory-selector` une brique indépendante et facilement intégrable :

```text
              AI AGENT ECOSYSTEM
                       │
                       ▼
              ┌─────────────────┐
              │ JEV MEMORY      │
              │ SELECTOR        │
              └─────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     Memory          Context        Tools
     Selection       Budget         Routing
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 Better Agents
```

**Principe directeur :**

> **Don't give agents more context. Give them the right context.**
