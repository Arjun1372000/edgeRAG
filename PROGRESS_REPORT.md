# EdgeRAG — Progress Report

**Project:** EdgeRAG — Edge-Optimized RAG and Localized Failure Mitigation for Automated Assembly Lines  
**Primary goal:** Build a practical, end-to-end, locally deployable RAG system using an SLM for industrial maintenance assistance.  
**Current stage:** ML → metadata-aware retrieval bridge established; SLM generation and expanded knowledge corpus are next.

---

## 1. Project Objective

EdgeRAG is being developed as a **fully local / edge-oriented predictive-maintenance assistance system**.

The system is not primarily a generic chatbot. Its core workflow is:

```text
Machine telemetry
      ↓
Predictive-maintenance model
      ↓
Machine condition / failure diagnosis
      ↓
RAG retrieval from local maintenance knowledge
      ↓
Local SLM generation
      ↓
Actionable maintenance report
      ↓
Maintenance engineer / operations user
```

A conversational troubleshooting interface may be added later as an optional interface, but it is not the core product requirement.

### Core technology requirements

| Component | Current direction |
|---|---|
| RAG framework | **LangChain — required** |
| Vector database | **Chroma** |
| Embeddings | Local, configurable; currently **Ollama `nomic-embed-text`** |
| LLM / SLM | Local Ollama model; must remain configurable |
| Backend | **FastAPI** |
| Frontend | HTML + CSS + JavaScript |
| Graph/orchestration | LangGraph currently **not required** |
| Deployment | Local / edge-oriented, no cloud dependency |
| Configuration | Models, document path, chunking, retrieval settings must be replaceable without changing application logic |

The project is intentionally designed so that the embedding model, SLM, and document corpus can be swapped later for benchmarking and edge-deployment experiments.

---

## 2. Current Repository / Working Structure

The original repository contained:

```text
edgeRAG/
├── data/
│   └── ai4i2020.csv
├── docs/
├── EDA_project2.ipynb
├── Review1_RAG.pptx
├── README.md
├── requirements.txt
├── index.html
├── styles.css
└── .gitignore
```

The implementation has since been expanded with modular application code. The working structure now includes these major areas:

```text
edgeRAG/
├── data/
│   └── ai4i2020.csv
├── docs/
│   ├── SOP-001 - Heat Dissipation Failure (HDF).txt
│   ├── SOP-002 - Tool Wear Failure (TWF).txt
│   ├── SOP-003 - Overstrain Failure (OSF).txt
│   ├── SOP-004 - Power Failure (PWF).txt
│   └── SOP-005 - Random Failure (RNF).txt
├── config/
│   └── config.yaml
├── models/
│   ├── failure_model.joblib
│   ├── fault_model.joblib
│   └── metadata.json
├── reports/
│   └── data_quality_report.json
├── src/
│   ├── data/
│   │   └── validation.py
│   ├── ingestion/
│   │   ├── loader.py
│   │   ├── splitter.py
│   │   ├── indexer.py
│   │   └── ingest.py
│   ├── models/
│   │   ├── train.py
│   │   ├── predictor.py
│   │   └── thresholds.py
│   ├── pipeline/
│   │   └── machine_condition.py
│   └── retrieval/
│       └── retriever.py
├── tests/
│   ├── test_validation.py
│   ├── test_model.py
│   ├── test_real_rows.py
│   ├── test_machine_condition.py
│   ├── test_retrieval.py
│   └── test_ml_to_retrieval.py
├── vectorstore/
├── EDA_project2.ipynb
├── Review1_RAG.pptx
├── README.md
├── requirements.txt
├── index.html
├── styles.css
└── .gitignore
```

Some frontend/API folders were planned as part of the final architecture but have not yet been implemented as the next functional layer.

---

## 3. Knowledge Corpus — Current State

The initial document corpus consists of five synthetic but structured industrial SOPs:

```text
SOP-001 → HDF — Heat Dissipation Failure
SOP-002 → TWF — Tool Wear Failure
SOP-003 → OSF — Overstrain Failure
SOP-004 → PWF — Power Failure
SOP-005 → RNF — Random Failure
```

The documents were expanded from minimal drafts into a semi-complete SOP format covering areas such as:

- purpose
- failure description
- symptoms / trigger conditions
- likely root causes
- immediate mitigation
- diagnostic checks
- escalation conditions
- restart conditions
- safety notes
- related parameters

The documents are deliberately replaceable because they are synthetic project data and will be expanded as the retrieval/evaluation requirements become clearer.

### Current indexing result

The first ingestion pipeline successfully produced:

```text
Documents loaded: 5
Chunks created: 21
Embedding model: nomic-embed-text
Embedding dimension: 768
Vectors stored in Chroma: 21
```

Chroma is persisted locally under:

```text
./vectorstore
```

### Metadata added to indexed chunks

The document loader now extracts metadata such as:

```text
source
filename
document_id
title
failure_code
applies_to
severity
document_type
```

This allows structured retrieval constraints in addition to semantic similarity.

---

## 4. Embedding / Chroma Design

The current configuration is local and replaceable.

Conceptually:

```text
docs/
  ↓
LangChain document loader
  ↓
recursive chunking
  ↓
Ollama embeddings
  ↓
Chroma persistent vector store
```

Current embedding baseline:

```yaml
embedding:
  provider: "ollama"
  model: "nomic-embed-text"
```

The model is intentionally configured rather than hardcoded into the application logic.

The project is not committed to `nomic-embed-text` as the final embedding model. Embedding models should remain replaceable so that later edge experiments can compare model size, latency, memory requirements and retrieval quality.

---

## 5. Retrieval Baseline and Learning

A first retrieval test was run with five manually constructed diagnostic queries.

Because the corpus only contained 21 chunks, `top_k=4` returned a large fraction of the available knowledge. This made the initial corpus useful as a smoke test but too small for meaningful RAG experimentation.

### Important retrieval finding

For a PWF machine condition, semantic-only retrieval initially returned:

```text
1. RNF chunk — 0.7093
2. PWF chunk — 0.7034
3. RNF chunk — 0.7033
4. RNF chunk — 0.6941
```

This demonstrated that generic semantic similarity can retrieve maintenance text that is topically similar but not the most appropriate fault-specific evidence.

### Metadata-aware retrieval

The retriever was subsequently changed to accept a `failure_code` filter.

With a PWF diagnosis:

```text
PWF diagnosis
    ↓
metadata filter: failure_code = PWF
    ↓
semantic similarity search within matching documents
```

The same event then returned:

```text
Rank 1 — PWF symptoms/trigger conditions — 0.7034
Rank 2 — PWF diagnostic checks — 0.6905
Rank 3 — PWF failure description — 0.6477
Rank 4 — PWF safety / related parameters — 0.4490
```

This is an effective first retrieval baseline.

However, the project should not permanently rely on strict failure-code filtering. The eventual corpus will contain related documents such as electrical safety procedures, inverter diagnostics and restart procedures that may be relevant to PWF without carrying `failure_code=PWF`.

The intended next retrieval architecture is therefore:

```text
MachineCondition
      ↓
semantic candidate retrieval
      +
structured metadata / diagnosis signals
      ↓
reranking / merging
      ↓
final context
```

Potential later experiments include MMR, hybrid retrieval, score thresholds and reranking.

---

## 6. AI4I 2020 Dataset / Predictive-Maintenance Layer

The repository contains:

```text
data/ai4i2020.csv
```

The dataset currently has **10,000 rows**.

It is being used as the machine telemetry / predictive-maintenance side of the project, while the `docs/` corpus provides maintenance knowledge for RAG.

The main sensor/input features used by the current ML pipeline are:

```text
Type
Air temperature [K]
Process temperature [K]
Rotational speed [rpm]
Torque [Nm]
Tool wear [min]
```

The overall failure target is:

```text
Machine failure
```

The failure-mode fields are:

```text
TWF
HDF
PWF
OSF
RNF
```

---

## 7. Dataset Validation Layer

A dedicated validation module was added rather than modifying the raw CSV.

The validation stage checks:

- required columns
- missing values
- duplicate rows
- valid machine types
- non-negative numeric values
- binary target/failure flags
- consistency between `Machine failure` and the individual fault flags

### Validation results

```text
Raw rows:                    10,000
Rows used for training:       9,973
Rows excluded:                   27
Duplicate rows:                   0
Invalid Type rows:                0
Invalid numeric rows:             0
Invalid binary label rows:       0
Label inconsistencies:           27
```

The raw failure-mode counts reported were:

```text
TWF: 46
HDF: 115
PWF: 95
OSF: 98
RNF: 19
```

Twenty-seven rows were excluded from training because the overall `Machine failure` flag did not agree with the individual fault flags.

Examples included rows with `RNF=1` but `Machine failure=0`, and rows with `Machine failure=1` but no fault flag set.

The raw CSV is preserved. The validator produces an audit report at:

```text
reports/data_quality_report.json
```

---

## 8. ML Architecture

The current ML layer has two concepts:

### A. Machine failure detection

A Random Forest classifier predicts:

```text
P(machine failure | sensor state)
```

The decision threshold is learned from a validation set instead of fixed at `0.5`.

The selected threshold is currently:

```text
0.220
```

The threshold-selection objective is F2, giving greater weight to recall.

### B. Known fault diagnosis

A One-vs-Rest Random Forest setup estimates fault-mode scores for:

```text
TWF
HDF
PWF
OSF
```

**RNF was removed from the learned fault classifier.**

Reason: the dataset provides extremely sparse RNF examples and there is no dependable telemetry signature for a genuinely random failure. RNF remains part of the knowledge corpus and validation/reporting, but an unexplained high-confidence machine failure is represented by the system as an unclassified / unknown failure condition rather than pretending RNF can be reliably predicted from sensor values.

---

## 9. Current ML Performance Baseline

After cleaning, validation-based threshold selection and retraining:

### Overall failure model

```text
Decision threshold: 0.220

Precision: 0.5873
Recall:    0.7400
F1:        0.6549
ROC-AUC:   0.9662
PR-AUC:    0.7343
```

The model's recall improved substantially from the original 0.5-threshold baseline. This is useful because the system is intended for failure detection where missed failures matter.

### Fault models

#### TWF

```text
Recall: 0.0000
ROC-AUC: 0.7372
PR-AUC: 0.0207
```

TWF is currently not a reliable learned fault detector.

#### HDF

```text
Recall: 0.9444
ROC-AUC: 0.9685
PR-AUC: 0.7774
```

HDF currently provides a useful diagnostic signal.

#### PWF

```text
Recall: 0.6923
ROC-AUC: 0.9986
PR-AUC: 0.8867
```

PWF currently provides a strong diagnostic signal.

#### OSF

```text
Recall: 0.9286
ROC-AUC: 0.9977
PR-AUC: 0.9040
```

OSF currently provides a strong diagnostic signal.

#### RNF

RNF is not part of the learned classifier anymore. Earlier experiments produced misleading metrics because random train/test splits can contain zero positive RNF examples. The system therefore treats RNF as an **unknown/unclassified failure path**, not as a reliable sensor-predicted class.

---

## 10. MachineCondition — ML → RAG Bridge

A structured handoff object was introduced between the predictive model and the RAG system.

The current `MachineCondition` contains:

```text
status
failure_probability
predicted_failure
diagnosis
fault_candidates
sensor_state
retrieval_query
```

Example observed condition:

```text
Status: CRITICAL
Failure probability: 0.925
Diagnosis: PWF
PWF score: 0.90
```

The generated retrieval query includes both:

1. the model diagnosis / failure probability
2. the observed machine parameters

For example:

```text
Industrial machine maintenance event.
Machine failure probability is 0.93.
Detected condition: PWF.
Retrieve relevant maintenance procedures, diagnostic checks,
mitigation actions, safety requirements, escalation conditions,
and restart requirements.
Observed machine parameters: air temperature 298.9 K,
process temperature 309.1 K, rotational speed 2861 RPM,
torque 4.6 Nm, tool wear 143 minutes.
```

This object is the planned interface between ML and RAG.

---

## 11. Current End-to-End Progress

The following chain now works:

```text
AI4I machine row
      ↓
Dataset validation
      ↓
Predictive-maintenance models
      ↓
MachineCondition
      ↓
Generated retrieval query
      ↓
Ollama embedding
      ↓
Chroma retrieval
      ↓
Relevant maintenance chunks
```

The **SLM generation step has not yet been connected**.

FastAPI and the final frontend have also not yet been implemented as the integrated application layer.

---

## 12. Current Configuration Philosophy

The project deliberately avoids hardcoding deployment choices wherever possible.

The configuration file controls items such as:

```yaml
documents:
  path: "./docs"

embedding:
  provider: "ollama"
  model: "nomic-embed-text"

chunking:
  chunk_size: 800
  chunk_overlap: 120

vectorstore:
  provider: "chroma"
  path: "./vectorstore"
  collection_name: "edge_rag"

retrieval:
  top_k: 4

model:
  artifacts_path: "./models"
  random_state: 42
  n_estimators: 200
  test_size: 0.15
  validation_size: 0.15

validation:
  exclude_inconsistent_labels: true

decision:
  threshold_beta: 2.0
  critical_threshold: 0.80
  primary_fault_min_probability: 0.35
```

The intent is that the following can be changed without rewriting the application:

- embedding provider/model
- SLM provider/model
- document corpus location
- chunk size/overlap
- Chroma persistence path/collection
- retrieval top-k
- ML decision thresholds
- model artifact location

---

## 13. Important Design Decisions

### RAG is not the failure detector

The predictive-maintenance model detects/characterizes the machine condition.

RAG supplies operational knowledge about:

- diagnosis
- mitigation
- diagnostics
- safety
- escalation
- restart

### The SLM is not the source of factual maintenance knowledge

The SLM should synthesize a response from retrieved local documents and machine-state context.

### Ollama is a local runtime option, not the definition of EdgeRAG

The architecture should remain capable of changing the local inference runtime later. Ollama is being retained because it is convenient for development and local model serving, but future edge experiments may compare other local runtimes and model formats.

### The project is not dependent on the internet at runtime

The intended edge deployment keeps:

```text
models
embeddings
vector database
RAG documents
API
frontend
```

local to the deployment environment.

### LangGraph is currently unnecessary

A standard LangChain RAG pipeline is sufficient for the present workflow. LangGraph can be reconsidered only if future requirements introduce genuine multi-step stateful orchestration that justifies it.

---

## 14. Current Limitations

### Corpus is too small

The current five-SOP / 21-chunk corpus is enough for smoke testing but not for meaningful retrieval benchmarking.

With only 21 chunks, `top_k=4` exposes too much of the corpus and does not adequately test difficult retrieval cases.

### TWF prediction is weak

The current model does not reliably identify TWF.

### RNF is not a learnable telemetry class

RNF is being treated as an unknown/unclassified failure path rather than a normal learned class.

### Failure model is still a baseline

A recall of 0.74 at the chosen threshold is useful for a baseline but not sufficient to claim production readiness.

### Probabilities are not yet calibrated

Random Forest `predict_proba` outputs are being used as relative confidence/decision scores. They should not yet be interpreted as perfectly calibrated real-world failure probabilities.

### RAG generation has not started

The retrieved chunks are not yet being passed to an SLM to generate the maintenance report.

### Frontend/API integration is incomplete

FastAPI and the final frontend workflow have not yet been connected to the live ML → RAG pipeline.

---

## 15. Immediate Next Milestones

### Milestone 1 — Corpus v2

Expand the synthetic industrial document corpus from the initial five SOPs into a semi-realistic maintenance knowledge base.

Target document categories:

```text
SOPs
Diagnostics
Maintenance
Safety
Restart / recovery
General failure investigation
Equipment / operating limits
Incident / case reports
```

The purpose is not simply to add documents, but to introduce realistic retrieval challenges:

- overlapping terminology
- related but non-identical documents
- information distributed across multiple documents
- supporting documents that lack an exact failure code
- multi-document maintenance questions

### Milestone 2 — Better retrieval architecture

Move from strict failure-code filtering to:

```text
semantic candidate retrieval
+
structured metadata signals
+
reranking / merging
```

Evaluate retrieval with a small labeled query set.

Potential metrics:

```text
Recall@1
Recall@3
Recall@5
MRR
```

### Milestone 3 — Local SLM generation

Connect the retrieved context to a configurable Ollama SLM.

The SLM should generate a structured maintenance report grounded in retrieved evidence.

### Milestone 4 — End-to-end RAG evaluation

Separate:

```text
retrieval quality
vs.
generation quality
vs.
end-to-end answer quality
```

### Milestone 5 — FastAPI

Expose endpoints for:

```text
machine-condition inference
RAG retrieval
maintenance report generation
health/status
```

### Milestone 6 — Frontend

Build a local maintenance dashboard showing:

- machine condition
- failure probability / confidence
- diagnosed fault
- sensor state
- retrieved evidence
- generated maintenance report

A chat/troubleshooting view may be added later as an optional interface.

### Milestone 7 — Edge benchmarking

Compare local model/runtime choices using:

```text
model size
memory usage
embedding latency
retrieval latency
LLM inference latency
end-to-end latency
answer quality
retrieval quality
```

This benchmarking layer is central to making the project genuinely about **RAG at the edge**, rather than simply being a local RAG demo.

---

## 16. Useful Commands Implemented So Far

### Validate dataset

```powershell
python -m tests.test_validation
```

### Train models

```powershell
python -m src.models.train
```

### Test model on selected real rows

```powershell
python -m tests.test_real_rows
```

### Test MachineCondition bridge

```powershell
python -m tests.test_machine_condition
```

### Re-index documents

```powershell
python -m src.ingestion.ingest
```

### Test retrieval

```powershell
python -m tests.test_retrieval
```

### Test ML → retrieval

```powershell
python -m tests.test_ml_to_retrieval
```

---

## 17. Current Overall Status

```text
[✓] Project objective defined
[✓] Local / edge-first architecture defined
[✓] LangChain selected
[✓] Chroma selected
[✓] Ollama selected as local development/runtime option
[✓] Configurable model/document architecture established
[✓] Initial SOP corpus created
[✓] Document ingestion implemented
[✓] Chunking implemented
[✓] Local embeddings implemented
[✓] Chroma persistence implemented
[✓] Retrieval baseline implemented
[✓] Metadata-aware retrieval implemented
[✓] AI4I dataset integrated
[✓] Dataset validation implemented
[✓] Failure prediction baseline implemented
[✓] Validation-based decision threshold implemented
[✓] Known-fault diagnosis baseline implemented
[✓] MachineCondition ML → RAG bridge implemented
[ ] Expand realistic document corpus
[ ] Build retrieval evaluation dataset
[ ] Build reranking / richer retrieval strategy
[ ] Connect Ollama SLM generation
[ ] Generate structured maintenance reports
[ ] Build FastAPI backend
[ ] Build frontend dashboard
[ ] Add end-to-end evaluation
[ ] Benchmark edge model/runtime tradeoffs
[ ] Package final local deployment
```

---

## 18. Current Project Definition

The project should ultimately demonstrate:

> **A configurable, fully local, edge-oriented predictive-maintenance RAG system that takes machine telemetry, detects or characterizes a failure condition, retrieves relevant industrial maintenance knowledge using Chroma and LangChain, and uses a lightweight local SLM to generate an actionable maintenance report for an engineer.**

The strongest technical contribution is expected to come from the combination of:

```text
predictive-maintenance inference
        +
structured condition representation
        +
metadata-aware / semantic retrieval
        +
local SLM generation
        +
edge-resource evaluation
```

rather than from any single model or framework in isolation.
