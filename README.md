# TaxIQ: AI-Powered Agentic Tax Assistant (FY 2025-26)

TaxIQ is an agentic tax planning assistant built using LangGraph and LangChain. It guides users in setting up, maintaining, and optimizing tax profiles for themselves and their family members, comparing Old vs. New tax regimes, and verifying deduction limits.

---

## Technical Implementation

### 1. Agent Architecture
*   **Core Engine**: Compiled using LangGraph's stateful orchestration. The agent processes messages, resolves tool calls, updates conversation state, and saves thread checkpoints.
*   **State & Configuration**: Maintained using `UserContext` for active users and LangGraph's configurations to track independent `thread_id` sessions.

### 2. Multi-Profile Storage Layer
*   **Profile Storage**: File-based storage (JSON schema) maps distinct relative/family member profiles (e.g. `Self`, `Mom`, `Dad`) under a user account.
*   **Smart Query Matching**: When querying or updating, the store automatically resolves target profiles by exact or substring match on names, relationships, or file IDs.
*   **Persistence Checkpointer**: Session progress and graph histories are persistently checkpointed via `SqliteSaver` connected to `checkpoints.db` with thread-safe connection pooling.

### 3. Tax Calculation Engine
*   **ITR-1 Calculations**: Computes gross income, standard deductions, HRA exemptions, and specific deductions under Chapter VI-A.
*   **Automatic HRA Exemption**: Calculates HRA exemption limit dynamically using the three standard Indian Tax rules:
    1. Actual HRA received.
    2. Rent paid minus 10% of basic salary.
    3. 50% of basic salary (for Metro cities: Chennai, Mumbai, Kolkata, Delhi) or 40% (for non-metro).
*   **Deduction Auditing**: Validates Chapter VI-A limits (e.g., Section 80C limit of ₹1.5L, Section 80D health insurance limits, Section 80CCD1B NPS limit of ₹50k, Section 24B home loan interest) and provides utilized vs. remaining balances.

### 4. Legal Tax Knowledge Base (RAG)
*   **Source Data**: Context index is built using parsed text and extracted tables from the **official Income Tax Act 2025 (as amended by Finance Act 2026)** PDF document.
*   **Retrieval**: Resolves user tax queries against the vector store using hybrid retrieval algorithms.

---

## Architectural Optimizations

*   **Model Fallback Middleware**: Automatically transitions from the primary model (`groq:llama-3.3-70b-versatile`) to a backup model (`google_genai:gemini-2.0-flash`) in case of API rate limits (HTTP 429) or service outages.
*   **Summarization Middleware**: Compresses conversation history once the message buffer exceeds 4,000 tokens, dynamically summarizing older messages while preserving the last 20 turns to protect context window limits.
*   **Tool Call Guardrails**: Caps maximum tool execution to 20 calls per thread and 10 per execution run to prevent expensive, recursive LLM tool-calling loops.
*   **Context Window Optimization**: Prunes repetitive tool call payloads using `ClearToolUsesEdit` in the middleware layer.
*   **RAG Retrieval & Reranking**: Maximizes accuracy of tax rule lookups using:
    *   *Hybrid Search*: Combined BM25 lexical search and ChromaDB vector embeddings.
    *   *Reciprocal Rank Fusion (RRF)*: Merges keyword and vector search rankings.
    *   *Transformer Reranker*: Rescores candidates to ensure the most relevant legal context is passed.

---

## Retrieval Engine Performance Evaluation

Evaluation of retrieval configurations (tested against a golden dataset of 20 representative queries across 4 categories, referencing chunk IDs from the official **Income Tax Act 2025 (as amended by Finance Act 2026)** document):

| Engine Configuration | Hit Rate (k=5) | Mean Reciprocal Rank (MRR) | Description |
| :--- | :---: | :---: | :--- |
| **BM25** | 85.0% | 0.6917 | Lexical keyword-based retrieval |
| **VECTOR** | 75.0% | 0.5683 | Dense vector search (Chroma + all-MiniLM-L6-v2) |
| **HYBRID** | 90.0% | 0.7600 | RRF combination of BM25 and Vector search |
| **RERANKED** | 85.0% | 0.7750 | Hybrid search filtered & re-ordered via Cross-Encoder |

*Key Takeaway: The **Reranked** configuration provides the highest search precision (MRR: 0.7750), placing correct reference documentation at rank 1 or 2 in almost all successful queries.*

---

## Project Directory Structure

```text
tax_assistant/
│
├── agents/                      # Agent configuration and middleware pipeline
│   ├── __init__.py
│   ├── agent.py                 # Agent initializer, env verification, and checkpointer setup
│   └── middleware.py            # Fallbacks, token summarization, and limit middlewares
│
├── prompts/                     # Prompt templates
│   ├── prompt_builder.py        # System prompt loading and caching utilities
│   └── tax_agent_system_prompt.txt # Master tax assistant instructions & guidelines
│
├── rag/                         # Retrieval-Augmented Generation module
│   ├── chroma_db/               # Local ChromaDB vector database files
│   ├── embeddings/              # Sentence-transformers embedding configurations
│   ├── retrieval/               # BM25, vector, and hybrid search retrievers
│   ├── reranker/                # Transformer reranking configurations
│   └── rag_pipeline.py          # Unified hybrid search and RAG orchestration
│
├── tools/                       # Calculation, checkers, and profile operations
│   ├── profiles/                # User and family relative profile JSON files (e.g. checkpoints)
│   ├── profile_store.py         # Multi-profile reader, writer, and match layer
│   ├── schemas.py               # Data models for UserProfile, StoredProfile, and TaxInputs
│   ├── tax_tools.py             # Agent tools for tax calculation and profile updates
│   ├── deduction_checker.py     # Section 80C, 80D, 80CCD1B, and HRA validation
│   ├── itr1_calculator.py       # ITR-1 tax slab calculations (Old vs. New regimes)
│   └── itr2_calculator.py       # ITR-2 capital gains & dividend tax computations
│
├── checkpoints.db               # Persistent SQLite session checkpoints database
├── pyproject.toml               # Project specifications and dependency mappings
└── uv.lock                      # Lockfile for precise package version resolution
```
