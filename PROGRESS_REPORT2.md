# EdgeRAG — Progress Report 2

**Continuation of:** `PROGRESS_REPORT.md`  
**Project:** EdgeRAG — Edge-Optimized RAG and Localized Failure Mitigation for Automated Assembly Lines  
**Current stage:** End-to-end local pipeline established through FastAPI/frontend; retrieval and SLM generation quality are now the main active engineering areas.

---

## 1. Continuation Summary

Since `PROGRESS_REPORT.md`, the project has moved from a basic five-document RAG smoke test to a substantially more complete local application.

The following components are now in place:

```text
AI4I machine data
      ↓
Data validation
      ↓
Predictive-maintenance model
      ↓
MachineCondition
      ↓
Condition-specific retrieval query
      ↓
Chroma retrieval
      ↓
Metadata-aware reranking
      ↓
Retrieved maintenance evidence
      ↓
Local Ollama SLM
      ↓
Maintenance report
      ↓
FastAPI
      ↓
Local browser frontend
```

The core project remains **fully local**. No cloud LLM or external API is required for the intended pipeline.

The project now has two important experimental observations:

1. **Metadata-aware / fault-aware retrieval is substantially more useful than pure semantic retrieval for this application.**
2. **The initial 1B SLM can produce a report, but it currently makes grounding and evidence-interpretation mistakes that make the generation layer unreliable for a maintenance workflow.**

The second point is now a key EdgeRAG experiment rather than a blocker: the project can measure whether different SLM sizes/runtimes improve grounded report generation under edge constraints.

---

# 2. Expanded Knowledge Corpus — Corpus v2

The original five-SOP corpus was intentionally too small for meaningful retrieval experiments.

A second corpus was therefore created with **21 synthetic industrial maintenance documents**.

The new corpus is organized as:

```text
docs/
├── sops/
├── diagnostics/
├── safety/
├── maintenance/
└── restart/
```

### Corpus categories

```text
sops/
    5 failure-specific SOPs

diagnostics/
    5 diagnostic procedures

safety/
    4 safety / isolation procedures

maintenance/
    5 supporting maintenance guides

restart/
    2 restart / return-to-service procedures
```

The corpus includes the original:

```text
SOP-001 → HDF
SOP-002 → TWF
SOP-003 → OSF
SOP-004 → PWF
SOP-005 → RNF
```

plus documents for:

- temperature diagnostics
- torque / overstrain diagnostics
- power / electrical diagnostics
- tool condition diagnostics
- general failure investigation
- electrical isolation / lockout-tagout
- emergency shutdown
- guarding / manual intervention
- telemetry integrity
- cooling maintenance
- tool replacement / spindle care
- inverter / motor maintenance
- preventive maintenance
- abnormal vibration inspection
- controlled restart
- post-failure verification

### Purpose of the expanded corpus

The purpose is not simply to increase document count.

It deliberately creates realistic retrieval challenges where a single machine event may require information from several document types.

For example, a PWF event may require:

```text
PWF SOP
+
power diagnostics
+
electrical isolation
+
inverter maintenance
+
restart procedure
+
post-failure verification
```

This makes retrieval quality much more meaningful than the original five-document / 21-chunk smoke test.

The corpus contains a `CORPUS_README.md` documenting its intended evaluation role.

> These documents are synthetic project artifacts for RAG development and evaluation. They are not real manufacturer procedures or safety instructions for physical deployment.

---

# 3. Chroma Re-indexing with Corpus v2

The existing ingestion pipeline supports nested directories through recursive file discovery.

After replacing the original corpus with Corpus v2, the same ingestion command is used:

```powershell
python -m src.ingestion.ingest
```

The ingestion pipeline continues to use:

```text
LangChain
    ↓
document loader
    ↓
recursive chunking
    ↓
Ollama embeddings
    ↓
Chroma
```

The Chroma database remains persisted locally under:

```text
./vectorstore
```

Because the current ingestion implementation resets the collection before indexing, the corpus can be replaced and re-indexed without accumulating stale chunks.

This reset-based approach is acceptable for the current small development corpus. Incremental indexing should be considered later if the corpus becomes large.

---

# 4. Metadata-Aware Document Representation

The document loader was upgraded so chunks retain structured metadata extracted from the documents.

Metadata currently includes fields such as:

```text
source
filename
document_id
title
failure_code
applies_to
severity
document_type
related_failure_codes
```

The `document_type` is derived from the document folder:

```text
sops        → sop
diagnostics → diagnostics
safety      → safety
maintenance → maintenance
restart     → restart
```

This gives the retrieval system structured signals in addition to embeddings.

For example:

```text
Power and Electrical Diagnostics.txt

document_type:
diagnostics

related_failure_codes:
PWF,RNF

severity:
Critical
```

while the primary PWF SOP contains:

```text
document_type:
sop

failure_code:
PWF

severity:
Critical
```

---

# 5. Retrieval Architecture — Current Version

The retrieval layer evolved in three stages.

## Stage 1 — Pure semantic search

The first implementation used:

```text
query
 ↓
embedding
 ↓
Chroma similarity search
 ↓
top-k
```

For a PWF event, pure semantic retrieval produced results such as:

```text
RNF chunk       0.7093
PWF chunk       0.7034
RNF chunk       0.7033
RNF chunk       0.6941
```

This showed that generic semantic similarity was not sufficient to guarantee useful fault-specific evidence.

---

## Stage 2 — Strict fault metadata filtering

A `failure_code` filter was then added.

For a PWF diagnosis:

```text
failure_code = PWF
```

The retriever correctly returned only PWF chunks.

That solved the fault-specific retrieval problem but introduced a new limitation:

> Relevant supporting documents could be excluded if they were related to PWF but were not themselves labeled as `PWF`.

For example:

```text
Electrical Isolation
Inverter Maintenance
Controlled Restart
```

may all be relevant even though they are not primary PWF SOP documents.

---

## Stage 3 — Global semantic retrieval + fault-aware reranking

The current retrieval design combines:

```text
Global semantic candidates
        +
fault-focused candidates
        ↓
candidate merge
        ↓
deduplication
        ↓
fault / metadata bonuses
        ↓
source diversification
        ↓
final top-k
```

Current retrieval configuration includes:

```yaml
retrieval:
  top_k: 6
  semantic_k: 12
  fault_k: 4
  max_chunks_per_source: 2

  reranking:
    fault_bonus: 0.12
    document_type_bonus: 0.03
    severity_bonus: 0.02
```

The implementation intentionally keeps these values configurable.

The system does not strictly restrict retrieval to the diagnosed fault. Instead, it allows relevant documents across the corpus while giving a controlled preference to documents related to the diagnosed condition.

---

# 6. Improved MachineCondition Query

The ML → RAG bridge was made more condition-specific.

Instead of generating only a generic request for:

```text
maintenance procedures
diagnostic checks
mitigation
safety
restart
```

the query now adds condition-specific context.

For PWF, the query includes the derived power proxy:

```text
Torque × Rotational Speed
```

For the tested PWF sample:

```text
RPM: 2861
Torque: 4.6
Power proxy: 13160.6
```

The generated query therefore explicitly states the diagnosed condition and the relevant evidence categories.

For example:

```text
Industrial machine maintenance event.
Machine failure probability is 0.93.
Detected condition: PWF.
Inferred power proxy from Torque × Rotational Speed is 13160.6.
Prioritize evidence related to power delivery,
electrical diagnostics, electrical isolation,
inverter faults, mitigation, escalation,
and controlled restart.
Observed machine parameters: ...
```

Equivalent condition-specific query terms are generated for:

```text
HDF
TWF
OSF
UNCLASSIFIED_FAILURE
```

This gives the embedding search a much more discriminative query.

---

# 7. Retrieval Result After Reranking

For the PWF test case:

```text
Status: CRITICAL
Failure probability: 0.925
Diagnosis: PWF
```

the current retrieval output became:

```text
Rank 1
SOP-004 - Power Failure (PWF).txt
Score: 0.9222

Rank 2
Power and Electrical Diagnostics.txt
Score: 0.8907

Rank 3
Post-Failure Verification Checklist.txt
Score: 0.8386

Rank 4
Inverter and Motor Electrical Maintenance Guide.txt
Score: 0.8244

Rank 5
Controlled Machine Restart Procedure.txt
Score: 0.8182

Rank 6
Preventive Maintenance Schedule Reference.txt
Score: 0.7974
```

This is materially more useful than the earlier semantic-only behavior.

The evidence set now contains:

```text
fault-specific SOP
+
diagnostic evidence
+
maintenance evidence
+
restart evidence
+
general maintenance context
```

This is the current retrieval baseline.

### Important interpretation

The scores shown in the test after reranking are **reranked retrieval scores**, not raw Chroma semantic similarity scores.

The system currently preserves the semantic score internally and applies configurable bonuses.

Future evaluation should separately track:

```text
raw semantic score
reranked score
```

so retrieval improvements can be quantified rather than judged only by visual inspection.

---

# 8. Local SLM Generation Layer

A generation module was added under:

```text
src/generation/
└── generator.py
```

The current LLM configuration is intended to remain replaceable:

```yaml
llm:
  provider: "ollama"
  model: "llama3.2:1b"
  temperature: 0.1
  num_predict: 600
```

The exact model remains a configurable experimental variable.

The current generator uses LangChain's Ollama chat integration and receives:

```text
MachineCondition
+
retrieved evidence
```

It does **not** receive internet context or external cloud information.

The generator prompt was tightened to require:

- evidence-grounded reporting
- no invented procedures
- no invented thresholds
- no unsupported causes
- distinction between model prediction and physical confirmation
- source identifiers such as `[S1]`, `[S2]`
- fixed report sections

The intended report structure is:

```text
# Maintenance Incident Report

## 1. Incident Summary

## 2. Observed Machine State

## 3. Diagnostic Assessment

## 4. Immediate Actions

## 5. Diagnostic Checks

## 6. Escalation

## 7. Restart / Return to Service

## 8. Evidence Sources
```

---

# 9. First End-to-End SLM Result

The complete local test now runs:

```text
AI4I row
  ↓
ML prediction
  ↓
MachineCondition
  ↓
Chroma retrieval + reranking
  ↓
Ollama SLM
  ↓
maintenance report
```

The first tested report successfully produced the expected general report format.

However, the report revealed important SLM limitations.

### Observed generation errors

The SLM incorrectly stated:

> "The calculated inferred machine power is below 3500 W"

while the MachineCondition query had already calculated:

```text
13160.6
```

and the PWF knowledge explicitly treats a critically high power condition above 9000 W as relevant.

The SLM also introduced unsupported claims such as:

- tool/spindle inspection being required simply from the supplied tool-wear value
- the machine being in a "normal operating state"

It also failed to reliably extract explicitly available:

- escalation requirements
- restart requirements

from the retrieved evidence, claiming that these were not explicitly stated.

### Current interpretation

This indicates:

```text
Retrieval quality:
Reasonably strong

SLM grounding / evidence interpretation:
Currently insufficient
```

This is an important EdgeRAG engineering result.

The initial 1B model should therefore be treated as a **generation baseline**, not as a production-ready report generator.

---

# 10. SLM Architecture Decision

The project should not immediately replace the 1B model with a larger model simply because the first report contained mistakes.

The project objective is specifically edge-oriented.

The intended experiment is:

```text
small SLM
      ↓
quality / grounding / latency / memory

larger SLM
      ↓
quality / grounding / latency / memory
```

Potential later model comparisons may include different Ollama-available SLM sizes.

The important question is:

> What is the smallest local model that produces sufficiently grounded maintenance reports from retrieved evidence?

The final model should therefore be selected experimentally, not assumed in advance.

---

# 11. FastAPI Backend

A FastAPI layer has now been added.

Planned working structure:

```text
api/
├── __init__.py
└── main.py
```

The backend currently exposes:

```text
GET  /api/health
GET  /api/sample
POST /api/analyze
GET  /
```

### `POST /api/analyze`

The current API pipeline is:

```text
JSON sensor input
      ↓
normalization
      ↓
MachineConditionBuilder
      ↓
EdgeRAGRetriever
      ↓
EdgeRAGGenerator
      ↓
JSON response
```

The response contains:

```text
machine_condition
evidence
report
report_html
```

This keeps both the original Markdown report and the presentation-ready HTML representation.

---

# 12. Local Frontend

A browser-based local dashboard was added under:

```text
frontend/
├── index.html
├── style.css
└── script.js
```

The frontend is intentionally **not a generic chatbot UI**.

It currently shows:

```text
Machine sensor inputs
        ↓
Model assessment
        ↓
Failure probability
        ↓
Diagnosis
        ↓
Fault candidates
        ↓
Retrieved evidence
        ↓
Maintenance report
```

### Current interaction

The user can:

1. Enter sensor values manually.
2. Load a failure sample from `ai4i2020.csv`.
3. Run the local EdgeRAG analysis.
4. View the machine condition.
5. View fault candidates.
6. Inspect retrieved evidence.
7. Read the generated maintenance report.

The frontend communicates with FastAPI locally.

No cloud endpoint is required.

---

# 13. Markdown Report Rendering

The generated report is retained as Markdown by the backend.

The API additionally converts it to HTML using Python's `markdown` package.

The response therefore contains:

```text
report
    → canonical Markdown

report_html
    → frontend presentation
```

The browser renders the HTML representation rather than displaying raw Markdown syntax.

The Markdown is still preserved as the underlying report format.

---

# 14. Current Frontend / Backend Architecture

The complete application now looks like:

```text
                  Browser
                     │
                     ▼
                  FastAPI
                     │
                     ▼
           MachineConditionBuilder
                     │
                     ▼
              ML prediction
                     │
                     ▼
              MachineCondition
                     │
                     ▼
               Retrieval query
                     │
                     ▼
          Chroma + Ollama embeddings
                     │
                     ▼
          fault-aware reranking
                     │
                     ▼
             Retrieved evidence
                     │
                     ▼
                Ollama SLM
                     │
                     ▼
             Markdown report
                     │
                     ▼
              HTML rendering
                     │
                     ▼
                  Browser
```

This is now a genuine end-to-end local application architecture rather than an isolated notebook experiment.

---

# 15. Current File / Module Responsibilities

The main implemented responsibilities are now:

```text
src/data/validation.py
    Dataset quality checks and clean training view

src/ingestion/loader.py
    Recursive document loading + metadata extraction

src/ingestion/splitter.py
    Recursive document chunking

src/ingestion/indexer.py
    Embedding creation + Chroma population

src/ingestion/ingest.py
    End-to-end corpus indexing entry point

src/models/train.py
    Failure and known-fault model training

src/models/thresholds.py
    Validation-based decision threshold selection

src/models/predictor.py
    Model inference and MachineCondition inputs

src/pipeline/machine_condition.py
    ML → structured condition → retrieval query

src/retrieval/retriever.py
    Semantic retrieval + fault-focused candidates +
    reranking + source diversification

src/generation/generator.py
    Local SLM report generation

api/main.py
    FastAPI application + local frontend serving

frontend/
    Local maintenance dashboard
```

---

# 16. Current Working Commands

### Validate dataset

```powershell
python -m tests.test_validation
```

### Train models

```powershell
python -m src.models.train
```

### Test model on real rows

```powershell
python -m tests.test_real_rows
```

### Test MachineCondition

```powershell
python -m tests.test_machine_condition
```

### Test retrieval

```powershell
python -m tests.test_retrieval
```

### Test ML → retrieval

```powershell
python -m tests.test_ml_to_retrieval
```

### Test full generation

```powershell
python -m tests.test_generation
```

### Re-index documents

```powershell
python -m src.ingestion.ingest
```

### Run FastAPI

```powershell
uvicorn api.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

---

# 17. Current Known Problems

## A. TWF prediction remains weak

Current test performance:

```text
TWF PR-AUC: 0.0207
Recall:     0.0000
```

The project should not present TWF as a reliable ML diagnosis.

Potential future handling:

- explicit domain rule support
- additional telemetry/features
- different modeling strategy
- threshold / calibration experiments
- treat tool-wear threshold as a domain condition in the event layer

---

## B. RNF is not treated as a learned sensor class

RNF remains in the dataset and knowledge corpus but is not trusted as a conventional sensor-predicted class.

The current intended path is:

```text
High failure probability
+
no sufficiently confident known fault
        ↓
UNCLASSIFIED_FAILURE
        ↓
general diagnostics / RNF knowledge
```

---

## C. Retrieval can still overvalue generic documents

The current reranker is deliberately lightweight.

It uses configurable bonuses rather than a learned reranker or cross-encoder.

Future experiments may compare:

```text
semantic only
vs
metadata-aware
vs
metadata-aware + reranking
vs
hybrid
vs
MMR
```

---

## D. SLM grounding is currently insufficient

The first 1B report contained multiple unsupported or incorrect statements despite good retrieved evidence.

Generation improvements that have not yet been fully implemented/tested include:

- adding derived metrics directly to `MachineCondition`
- presenting sensor values in a more structured prompt format
- stricter evidence-to-statement requirements
- stronger source citation constraints
- explicit separation between model-derived information and document-derived information
- comparison of different SLM sizes
- possible post-generation validation

---

## E. Probability outputs need careful terminology

Random Forest `predict_proba()` values should not automatically be described as perfectly calibrated real-world probabilities.

The current system should interpret them as:

```text
model probability / estimated probability / score
```

until calibration is explicitly evaluated.

A future experiment can use probability calibration if it materially improves operational decision-making.

---

## F. AI4I is a prototype / synthetic industrial dataset

The AI4I dataset is being used as the predictive-maintenance prototype input.

The application narrative should not imply that this dataset contains real conveyor-belt-roller telemetry.

For the project narrative, the safer interpretation is:

> AI4I provides a synthetic industrial machine telemetry scenario representing an automated production asset.

A future version could replace the data source with real or higher-fidelity equipment telemetry without changing the overall EdgeRAG architecture.

---

# 18. Current Product Definition

The product is now defined as:

> **A fully local predictive-maintenance assistance system that receives machine telemetry, estimates machine failure/condition, retrieves relevant maintenance knowledge from a local Chroma knowledge base, and uses a local SLM to generate an evidence-grounded maintenance report for a maintenance engineer.**

The frontend is the local operating interface.

A chatbot is **not** required for the core product.

An optional interactive troubleshooting mode can be added later using the same local RAG infrastructure if it improves the practical workflow.

---

# 19. Current End-to-End Product Flow

The intended production-style workflow is now:

```text
Machine telemetry
      │
      ▼
Data validation
      │
      ▼
Failure prediction
      │
      ▼
Fault / condition assessment
      │
      ▼
MachineCondition
      │
      ▼
Condition-specific retrieval query
      │
      ▼
Global semantic retrieval
      +
fault-aware candidate retrieval
      │
      ▼
Reranking / diversification
      │
      ▼
Evidence set
      │
      ▼
Local SLM
      │
      ▼
Maintenance report
      │
      ▼
FastAPI
      │
      ▼
Local dashboard
      │
      ▼
Maintenance engineer
```

---

# 20. Next Engineering Priorities

The next work should proceed in this order.

### Priority 1 — Improve MachineCondition

Add explicitly structured derived metrics, for example:

```text
power_proxy
temperature_delta
condition-specific indicators
```

so the SLM receives them as structured data instead of needing to infer them.

### Priority 2 — Improve SLM grounding

Repeat the PWF generation test after the structured-condition changes.

The report should be checked for:

```text
factual correctness
evidence support
unsupported claims
wrong numerical interpretation
missing escalation requirements
missing restart requirements
```

### Priority 3 — Build a real RAG evaluation set

Create approximately 30–50 domain questions with known expected evidence.

Measure:

```text
Recall@1
Recall@3
Recall@5
MRR
```

and separate:

```text
retrieval performance
generation performance
end-to-end performance
```

### Priority 4 — Expand evaluation beyond one PWF case

Run complete end-to-end tests for:

```text
HDF
PWF
OSF
TWF
UNCLASSIFIED_FAILURE / RNF path
NORMAL
```

TWF and RNF should be treated as special cases rather than silently presenting weak model outputs as reliable diagnoses.

### Priority 5 — Compare SLM sizes

Only after the prompt and evidence pipeline are stable:

```text
smallest candidate SLM
        vs
medium small SLM
        vs
larger local SLM
```

Measure:

```text
report quality
groundedness
hallucination / unsupported claims
latency
RAM usage
model size
```

This is the part that will give the project its strongest **Edge AI engineering story**.

### Priority 6 — Add application-level evaluation

Expose metrics through the API or evaluation scripts and eventually summarize:

```text
retrieval quality
generation quality
latency
resource usage
```

This turns EdgeRAG from a working demo into a measurable engineering project.

---

# 21. Current Overall Status

### Working

```text
✓ Local document ingestion
✓ Configurable embedding model
✓ Ollama embeddings
✓ Chroma persistence
✓ Recursive document chunking
✓ Structured document metadata
✓ AI4I data validation
✓ Predictive failure model
✓ Known fault-model baseline
✓ Threshold tuning
✓ MachineCondition bridge
✓ Condition-specific retrieval query
✓ Semantic retrieval
✓ Fault-aware retrieval
✓ Lightweight reranking
✓ Source diversification
✓ Local Ollama SLM generation
✓ FastAPI backend
✓ Local HTML/CSS/JS frontend
✓ Markdown report generation/rendering
```

### Needs improvement

```text
△ TWF ML diagnosis
△ RNF / unclassified event strategy
△ SLM grounding and factual reliability
△ Retrieval evaluation methodology
△ SLM/model comparison
△ Latency / RAM / edge-resource benchmarking
△ End-to-end evaluation across all conditions
```

### Not yet implemented

```text
□ Formal retrieval benchmark dataset
□ Formal report-quality evaluation
□ Edge resource benchmark
□ Model-size comparison
□ Production-quality error handling / observability
□ Packaging / deployment strategy
□ Optional incremental document indexing
```

---

# 22. Recommended Immediate Next Step

Do **not** add more architectural components yet.

The most valuable immediate experiment is:

```text
Current PWF MachineCondition
        ↓
Current top-6 evidence
        ↓
Improved structured prompt
        ↓
Same SLM
        ↓
Compare report quality
```

Only after this baseline is improved should EdgeRAG move into:

```text
evaluation
→ SLM comparison
→ edge benchmarking
→ packaging/deployment
```

This keeps the project focused on its main research/engineering question:

> **How effectively can a lightweight, fully local RAG system transform machine-condition information and local maintenance knowledge into a useful, evidence-grounded maintenance response under edge constraints?**
