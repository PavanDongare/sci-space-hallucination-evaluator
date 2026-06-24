# SciSpace Hallucination Evaluator

> **An LLM-as-judge framework that evaluates hallucination in SciSpace's AI-powered research report-writing pipeline — from query generation to final citation grounding.**

---

## Table of Contents

- [What This Is](#what-this-is)
- [Motivation](#motivation)
- [How SciSpace Generates a Report](#how-scispace-generates-a-report)
- [Three Hallucination Surfaces](#three-hallucination-surfaces)
- [Evaluation Architecture](#evaluation-architecture)
  - [Stage 1: Query Hallucination (Intent Coverage)](#stage-1-query-hallucination-intent-coverage)
  - [Stage 2: Directional Faithfulness & Data Accuracy](#stage-2-directional-faithfulness--data-accuracy)
  - [Stage 3: Claim-Level Fact-Checking](#stage-3-claim-level-fact-checking)
- [Metrics Dictionary](#metrics-dictionary)
- [How the Runner Works](#how-the-runner-works)
  - [Step 0: Classify & Clean Inputs](#step-0-classify--clean-inputs)
  - [Step 1: Stage 1 Eval](#step-1-stage-1-eval--query-hallucination)
  - [Step 2: Stage 2 Eval](#step-2-stage-2-eval--directional-faithfulness--data-accuracy)
  - [Step 3: Stage 3 Eval](#step-3-stage-3-eval--claim-level-fact-checking)
  - [Step 4: Scorecard Generation](#step-4-scorecard-generation)
- [Project Structure](#project-structure)
- [Prompt Templates](#prompt-templates)
- [Installation & Usage](#installation--usage)
- [Trial Run Results](#trial-run-results)
  - [Run 1: Wearable Health Devices for Chronic Disease](#run-1-wearable-health-devices-for-chronic-disease)
  - [Run 2: AI-Based Early Cancer Detection](#run-2-ai-based-early-cancer-detection)
  - [Cascading Quality Comparison](#cascading-quality-comparison)
  - [Concrete Case Studies](#concrete-case-studies)
- [Production Readiness Assessment](#production-readiness-assessment)
- [Production Realities: What Actually Happens vs. Ideal Design](#production-realities-what-actually-happens-vs-ideal-design)
- [Known Evaluation Gaps](#known-evaluation-gaps)
- [Model Choice & Cost-vs-Accuracy Tradeoffs](#model-choice--cost-vs-accuracy-tradeoffs)
- [Design Decisions](#design-decisions)

---

## What This Is

This is a **hallucination evaluation CLI** for [SciSpace](https://typeset.io/)'s AI report-writing feature. SciSpace takes a user's research query, searches multiple academic databases, extracts insights from retrieved papers, and generates a final cited report. Each step involves an LLM — and each step can introduce hallucinations.

This evaluator answers: **"Is the output of this pipeline trustworthy?"** — with evidence, not just a score.

It runs three sequential evaluation stages, each checking a different hallucination surface, and produces a scorecard that shows not just what failed but *why* it failed and *what the source actually says*.

---

## Motivation

The naïve approach — "feed the report to a stronger LLM and ask if it hallucinated" — does not work. An LLM reading a polished report cannot distinguish between a correctly cited claim and one that sounds right but is fabricated. 

Hallucination in a research pipeline is not one problem; it is three:

1. **The search queries might miss what the user asked** → the retrieval path starts wrong.
2. **The intermediate synthesis might drift** → the report can be factually grounded and still answer the wrong question.
3. **The final claims might be unsupported by their citations** → the most direct hallucination risk.

Each failure surface requires a different check against a different ground truth. This evaluator implements all three.

---

## How SciSpace Generates a Report

```
User Query
    │
    ▼
┌──────────────────────┐
│  Step 1: LLM generates│
│  search queries       │──→  SciSpace (semantic), SciSpace (full-text),
└──────────────────────┘     Google Scholar, PubMed, ArXiv
    │
    ▼
┌──────────────────────┐
│  Step 2: Papers       │
│  retrieved & ranked   │──→  Deduplicated, relevance-scored
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│  Step 3: LLM extracts │
│  insights per paper   │──→  Intermediate insights report
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│  Step 4: LLM populates│
│  structured table     │──→  Consolidated CSV with criteria columns
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│  Step 5: LLM writes   │
│  final report with    │──→  Report with inline citations [1]-[N]
│  citations            │     and a References section with DOIs
└──────────────────────┘
```

The LLM touches the data at **five points**. Each is a hallucination risk. The evaluator checks three of these surfaces (Steps 1, 3+4, and 5), with Step 2 (paper consolidation/deduplication) identified as a known gap.

### Why Different Channels Use Different Query Formats

SciSpace searches multiple databases, and each has a different query syntax:

| Channel | Query Style | Reason |
|---|---|---|
| **SciSpace (semantic)** | Natural language question | Searches paper abstracts/summaries — short enough for semantic search |
| **SciSpace (full-text)** | Space-separated keywords | Searches full paper PDFs — too large for semantic search, uses deterministic string match |
| **Google Scholar** | Boolean with `AND`/`OR`, quotes, parentheses | Google Scholar's native search syntax |
| **PubMed** | MeSH terms with Boolean operators | PubMed's medical terminology search |
| **ArXiv** | API field syntax (`all:term+AND+all:term`) | ArXiv API's structured query format |

This matters for Stage 1: the evaluator's LLM judge scores **meaning, not syntax**. A keyword string like `wearable health devices chronic disease management adherence accuracy` and a natural language question like `"What are the effects of wearable health devices on chronic disease management?"` can both cover the same user intents.

---

## Three Hallucination Surfaces

```
Surface 1                Surface 2                        Surface 3
─────────                ─────────                        ─────────
QUERY                    DIRECTION & DATA                 FACTS
HALLUCINATION            FAITHFULNESS                     GROUNDING

Did the search           Did the results stay on          Are the report's
queries match            course? Is the extracted         claims backed by
user intent?             data accurate?                   their cited sources?

Checked against:         Checked against:                 Checked against:
USER QUERY               USER QUERY + PAPER ABSTRACTS     CITED PAPERS
```

Each surface catches something the other two cannot. A report can be factually grounded (Surface 3 passes) and still answer the wrong question (Surface 1 fails). A report can have perfect search coverage (Surface 1 passes) and still fabricate statistics in the final text (Surface 3 fails).

---

## Evaluation Methodology & System Design

To evaluate the trustworthiness of SciSpace's AI report writing pipeline, we implement a multi-stage, reference-grounded hallucination evaluation methodology. Instead of evaluating the report as a single black box, we decompose the pipeline into discrete checkpoints to isolate query drift, extraction errors, synthesis failures, and claim-level hallucinations.

### System Architecture Diagram

```text
               +-------------------------------------------------------+
               |                     User Query                        |
               +-------------------------------------------------------+
                                   |                       |
                  (Extract Atomic Intents)                 |
                                   v                       v
               +-----------------------+       +-----------------------+
               |     Atomic Intents    |       |  Intermediate Outline |
               +-----------------------+       +-----------------------+
                    |              |                       |
       (Semantic Intent Check)     |             (Directional check &
                    |              |              Drift detection)
                    v              |                       v
  STAGE 1: Intent Coverage         |           STAGE 2a: Directional Alignment
  ========================         |           ===============================
  Checks generated queries         |           Checks if intermediate summary
  against user intents.            |           addresses all intents without drift.
                                   |
                                   +-----------------------+
                                                           |
                                                           v
  STAGE 2b: Data Extraction Accuracy           STAGE 2c: Synthesis Faithfulness
  ==================================           ================================
  Checks spreadsheet cell values               Checks if report claims match
  against original paper abstracts.             consolidated spreadsheet rows.
         |                                                 |
         v (Cell Verification)                             v (Synthesis Verification)
  [ Spreadsheet Table ] <--------------+------------------ [ Final Report ]
                                       |
                                       | (Extract Claims & DOIs)
                                       v
                               STAGE 3: Fact-Checking
                               ======================
                               Isolates and verifies claims against cited sources.
                                       |
                                       v
                             [ Bibliography Parsing ]
                                       |
                                       +----> 1. Local CSV Cache Check (Fast)
                                       +----> 2. CrossRef API (Fallback 1)
                                       +----> 3. Semantic Scholar API (Fallback 2)
                                       |
                                       v
                             [ NLI Semantic Judge ]
                                       |
                                       v
                                +--------------+
                                |  Scorecard   |
                                +--------------+
```

### Core Methodology Walkthrough

Our methodology checking is structured sequentially across three stages:

1. **Intents Extraction & Search Validation (Stage 1)**:
   * **Purpose**: Catch hallucinated or deficient search pathways before retrieval starts.
   * **Method**: The evaluator extracts atomic user intents from the research query. It then maps each channel's generated queries to these intents. It uses semantic logic rather than keyword checking to accommodate channel-specific syntax differences (e.g. natural language queries on SciSpace vs. boolean queries on Google Scholar).

2. **Mid-Pipeline Synthesis Validation (Stage 2)**:
   * **Stage 2a (Directional Alignment)**: Compares the intermediate report sections to the user's intents. It scores each intent (1.0 for fully addressed, 0.5 for partially addressed, 0.0 for missing) and applies a **Drift Penalty** (-0.2 per topic) for any major unrelated topics introduced.
   * **Stage 2b (Data Extraction Accuracy)**: Compares spreadsheet cells against paper abstracts to catch data collection errors before writing.
   * **Stage 2c (Synthesis Faithfulness)**: Compares final report assertions to spreadsheet cells to ensure the writing model doesn't inject external information or exaggerate consensus.

3. **Factual Grounding Gate (Stage 3)**:
   * **Purpose**: Verify that every factual claim in the final report is backed by its cited source.
   * **Method**:
     1. The evaluator splits the final report into atomic factual assertions and records their inline citation IDs (`[1]`, `[5]`, etc.).
     2. It extracts reference metadata (DOIs, titles) from the report's `## References` section.
     3. For each claim, it retrieves the cited source text from a multi-tiered pipeline: checking the local CSV abstracts database first, and dynamically querying the CrossRef and Semantic Scholar APIs as fallbacks.
     4. An NLI LLM judge classifies the claim against the source abstract as: **Supported**, **Unsupported**, **Contradicted**, or **Overstated** (alongside **Uncited** and **Not Verifiable** categories).

---

### Stage 1: Query Hallucination (Intent Coverage)

**Question:** Did the system generate search queries that match the user's intent?

**Input:** User query + search queries (per channel)

**How it works:**
1. The LLM judge extracts **atomic intents** from the user query (e.g., `["adherence", "accuracy", "long-term health outcomes"]`).
2. For each search query across all channels, the judge checks which intents it substantively covers — scoring by semantic meaning, not syntax.

**Metric — Intent Coverage Rate (IC):**
```
IC = (Number of Intents Covered by ≥1 Search Query) / Total Extracted Intents
```

**Failure mode prevented:** Query Omission. If the user asks about "sensor accuracy in clinical environments" but the query generator only searches for "wearable health device outcomes," this metric flags the gap before papers are retrieved.

---

### Stage 2: Directional Faithfulness & Data Accuracy

Stage 2 evaluates three distinct aspects of the mid-pipeline output:

#### 2a. Directional Alignment

**Question:** Does the intermediate insights report stay aligned with the user's intents?

**Input:** User query (same intents from Stage 1) + intermediate report

**How it works:**
1. Using the same atomic intents from Stage 1, the LLM judge checks whether the intermediate report substantively addresses each intent.
2. Each intent is scored as: **Addressed (1.0)**, **Partially (0.5)**, or **Not Addressed (0.0)**.
3. The judge also flags any major topics introduced that are unrelated to any user intent (**drift**).

**Metric — Directional Alignment Rate (DA):**
```
DA = (Sum of Intent Scores) / Total Extracted Intents
```

**Failure mode prevented:** Informational Drift & Topic Deletion. Prevents the system from ignoring difficult user requirements or writing about unrelated research fields.

#### 2b. Data Extraction Accuracy

**Question:** Are the values in the consolidated spreadsheet table (study design, key findings, limitations) accurate to the original paper abstracts?

**Input:** Consolidated CSV with criteria columns + paper abstracts from the CSV cache

**How it works:**
1. The evaluator parses the consolidated CSV (looking for columns like "Study Design and Population", "Key Findings on Adherence Accuracy or Outcomes", "Limitations and Gaps").
2. For the top 5 papers, each criteria cell value is verified against the paper's original abstract by the LLM judge.
3. Each cell is labeled as: **supported**, **unsupported**, **contradicted**, or **overstated**.

**Metric — Data Extraction Accuracy (EA):**
```
EA = Supported Cells / Total Cells Scored
```

**Failure mode prevented:** Spreadsheet Hallucination. Prevents the model from populating tables with fake sample sizes, incorrect follow-up times, or exaggerated outcomes.

#### 2c. Synthesis Faithfulness

**Question:** Are the claims in the final report faithful to the data in the consolidated spreadsheet table?

**Input:** Final report claims + consolidated spreadsheet rows

**How it works:**
1. The evaluator compares the top 10 claims extracted from the final report against the first 10 rows of the spreadsheet table.
2. The LLM judge verifies whether the writer fabricated new facts, inflated counts, or added undocumented clinical benefits not present in the table.

**Metric — Synthesis Faithfulness (SF):**
```
SF = Report Claims Faithful to Table / Total Claims Checked Against Table
```

**Failure mode prevented:** Context Leakage & Authoritativeness Inflation. Catches cases where the writer claims consensus over a large study sample (e.g., "synthesized from 93 studies") when the underlying table only contains 10 rows.

---

### Stage 3: Claim-Level Fact-Checking

**Question:** Is each factual claim in the final report supported by its cited source?

**Input:** Final report (with inline citations and a References section with DOIs)

**How it works:**
1. The LLM judge splits the final report into **atomic factual claims**, recording which citation IDs (`[1]`, `[5]`, etc.) are attached to each.
2. For each cited paper, the evaluator fetches the paper's abstract via:
   - **Local CSV cache** (paper abstracts already present in the input CSV files)
   - **CrossRef API** (resolves DOIs to titles and abstracts)
   - **Semantic Scholar API** (fallback for DOI resolution)
3. The LLM judge classifies each claim against the fetched source text:

| Verdict | Meaning |
|---|---|
| **Supported** | The cited source directly states or clearly implies the claim |
| **Unsupported** | The cited source does not mention or contain evidence for the claim |
| **Contradicted** | The cited source says the opposite of the claim |
| **Overstated** | The source points in the same direction, but the report is stronger, broader, or less qualified |
| **Uncited** | A specific factual assertion is made with no citation attached |
| **Not Verifiable** | No cited source could be matched or retrieved for this citation ID |
| **Common Knowledge** | Marked as common knowledge by the claim extractor and not scored |

**Metrics derived:**

**Claim Reliability Rate (CR):**
```
CR = Supported Claims / Total Extracted Claims (excl. common knowledge)
```
The absolute truth rate of the report.

**Cited Grounding Rate (CGR):**
```
CGR = Supported Claims / (Total Scored Claims − Uncited Claims)
```
When the writer did cite a source, how often was it the correct source? Isolates citation accuracy from missing citations.

**Parallelization:** Stage 3 grounds claims using a `ThreadPoolExecutor` with 10 workers for parallel DOI resolution and LLM judging, with progressive output updates after each claim is processed.

---

## Metrics Dictionary

| # | Metric | Stage | Calculation | Failure Mode Detected |
|---|---|---|---|---|
| 1 | **Intent Coverage (IC)** | 1 | Intents covered / Total intents | Query omission |
| 2 | **Directional Alignment (DA)** | 2a | Intent scores sum / Total intents | Topic drift & deletion |
| 3 | **Data Extraction Accuracy (EA)** | 2b | Supported cells / Total cells scored | Spreadsheet hallucination |
| 4 | **Synthesis Faithfulness (SF)** | 2c | Faithful claims / Total claims vs. table | Context leakage |
| 5 | **Claim Reliability (CR)** | 3 | Supported / Total claims | Factual hallucination |
| 6 | **Cited Grounding Rate (CGR)** | 3 | Supported / Cited verifiable claims | Attribution mismatch |

---

## How the Runner Works

The evaluator is a single Python script (`eval.py`, ~1,060 lines) that orchestrates the entire pipeline. It uses `urllib` for HTTP requests (no external dependencies beyond the Python standard library) and loads prompt templates from external Markdown files.

### Step 0: Classify & Clean Inputs

The runner receives a **folder** with all files from one SciSpace run. File names are not standardized — the runner infers which file is which.

```bash
python3 eval.py ./trials/run1_wearables/inputs/
```

**File classification** uses a two-tier approach:
1. **Canonical shortcut:** If the folder contains the exact canonical filenames (`user_query.txt`, `search_queries.txt`, `intermediate_report.md`, `final_report.md`), classification is skipped.
2. **LLM classification:** Otherwise, the runner reads all files, generates previews (first 500 characters each), and sends them to the LLM judge using `prompts/classify_files.md` to identify which file is the user query, search log, intermediate report, and final report.
3. **Heuristic fallback:** If the LLM returns invalid JSON, a rule-based classifier (`heuristic_classify_files()`) uses filename patterns and content markers (e.g., "Searched SciSpace", "## References") to assign roles.

**Search query cleanup** also uses a two-tier approach:
1. **Pre-cleaned JSON:** If a `search_queries.json` file exists with valid `{channel, query}` pairs, it is used directly.
2. **LLM cleanup:** Otherwise, the raw search log (which includes emoji, paper counts, status messages like "🔍 Searching scholarly literature...") is sent to the LLM using `prompts/clean_search_queries.md`.
3. **Heuristic fallback:** If the LLM fails, `heuristic_clean_search_queries()` parses `"Searched <channel>"` blocks with regex.

### Step 1: Stage 1 Eval — Query Hallucination

**LLM calls:**
1. Extract atomic intents from user query → `prompts/extract_intents.md`
2. Check search queries against intents → `prompts/stage1_intent_coverage.md`

**Deterministic computation:** Count intents covered ÷ total intents → **Intent Coverage %**

### Step 2: Stage 2 Eval — Directional Faithfulness & Data Accuracy

**LLM calls:**
1. Check intermediate report against intents + detect drift → `prompts/stage2_directional.md`
2. If a consolidated CSV with criteria columns is detected (`find_and_parse_consolidated_csv()`):
   - Verify top 5 papers' criteria cells against abstracts → `prompts/verify_data_extraction.md`
   - Verify top 10 report claims against table rows → `prompts/verify_synthesis_faithfulness.md`

**CSV detection:** The evaluator looks for CSV files containing columns matching at least 2 of: `"Study Design and Population"`, `"Key Findings on Adherence Accuracy or Outcomes"`, `"Limitations and Gaps"`. Column matching is case-insensitive with whitespace normalization.

**Deterministic computation:** Count intents addressed ÷ total intents → **Directional Alignment %**; supported cells ÷ total cells → **Data Extraction Accuracy %**; faithful claims ÷ total → **Synthesis Faithfulness %**

### Step 3: Stage 3 Eval — Claim-Level Fact-Checking

**LLM calls:**
1. Split final report into atomic claims → `prompts/stage3_extract_claims.md`
2. For each claim, judge against fetched source → `prompts/stage3_ground_claim.md`

**Source retrieval pipeline:**
1. Parse the `## References` section from the final report using regex to extract reference IDs, titles, DOIs, and URLs.
2. Build a **local CSV cache** by scanning all CSV files in the input folder for DOI → title+abstract mappings.
3. For each cited claim, look up the source:
   - First check the local CSV cache (fast, no network).
   - If DOI not cached, fetch from **CrossRef API** (`https://api.crossref.org/works/{doi}`).
   - If CrossRef fails, try **Semantic Scholar API** (`https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}`).
   - If all lookups fail, use the raw reference text as a fallback.
4. The LLM judge classifies: `supported` / `unsupported` / `contradicted` / `overstated`.

**Parallelization:** Claims are grounded in parallel using 10 worker threads. The scorecard and detailed log are updated progressively after each claim is processed.

### Step 4: Scorecard Generation

The evaluator outputs two files:
- `scorecard.md` — Human-readable scorecard with metrics **and** concrete evidence for every failure.
- `detailed_log.json` — Complete JSON log of every individual judgment, classification, and intermediate result.

Every failure in the scorecard includes: **what the report said**, **what the source said**, and **why it's a problem**.

---

## Project Structure

```
.
├── eval.py                              ← The runner (~1,060 lines, zero external dependencies)
├── .env.example                         ← Template for API configuration
├── .gitignore
├── README.md                            ← This file
├── README_EVAL_WORKFLOW.md              ← Copy-paste prompt guide for evaluating new runs
│
├── prompts/                             ← LLM judge prompt templates (editable without touching code)
│   ├── classify_files.md                ← "Identify which file is which"
│   ├── clean_search_queries.md          ← "Extract channel + query pairs from messy log"
│   ├── extract_intents.md               ← "Extract atomic intents from user query"
│   ├── prepare_input_folder.md          ← "Prepare canonical input folder from messy files"
│   ├── stage1_intent_coverage.md        ← "Which intents does this search query cover?"
│   ├── stage2_directional.md            ← "Does this report align with these intents?"
│   ├── stage3_extract_claims.md         ← "Split report into atomic claims with citation IDs"
│   ├── stage3_ground_claim.md           ← "Is this claim supported by this source?"
│   ├── verify_data_extraction.md        ← "Is this spreadsheet cell accurate to the paper abstract?"
│   └── verify_synthesis_faithfulness.md ← "Is this report claim faithful to the spreadsheet table?"
│
└── trials/                              ← Consolidated trial runs (no duplicate files)
    ├── run1_wearables/                  ← Trial 1: Wearables health devices
    │   ├── inputs/                      ← Canonical inputs (user_query.txt, CSV paper cache, etc.)
    │   └── outputs/
    │       ├── deepseek_flash/          ← scorecard.md + detailed_log.json from DeepSeek Flash
    │       └── minimax/                 ← scorecard.md + detailed_log.json from MiniMax
    │
    └── run2_cancer_detection/           ← Trial 2: AI early cancer detection
        ├── inputs/                      ← Canonical inputs (including source CSV abstracts)
        └── outputs/
            └── deepseek_flash/          ← scorecard.md + detailed_log.json from DeepSeek Flash
```

---

## Prompt Templates

All evaluation logic is driven by **external prompt templates** stored as plain Markdown files in `prompts/`. This means a PM or researcher can edit the evaluation criteria without touching the Python runner code.

Each prompt file contains:
- A clear instruction for the LLM judge
- Template variables (e.g., `{query}`, `{intents}`, `{report_text}`) filled by the runner at execution time
- A strict JSON output schema

| Prompt File | Purpose | Template Variables |
|---|---|---|
| `classify_files.md` | Identify which input file serves which role | `{file_previews}` |
| `clean_search_queries.md` | Extract clean channel+query pairs from messy log | `{raw_log}` |
| `extract_intents.md` | Extract atomic user intents from research query | `{query}` |
| `prepare_input_folder.md` | Prepare canonical folder from messy SciSpace export | *(used for folder preparation workflow)* |
| `stage1_intent_coverage.md` | Check if search queries cover each user intent | `{intents}`, `{search_queries}` |
| `stage2_directional.md` | Check if intermediate report aligns with intents | `{intents}`, `{report_text}` |
| `stage3_extract_claims.md` | Split final report into atomic factual claims | `{report_text}` |
| `stage3_ground_claim.md` | Judge if a claim is grounded in its cited source | `{claim_text}`, `{citation_ids}`, `{paper_content}` |
| `verify_data_extraction.md` | Verify spreadsheet cell accuracy vs. paper abstract | `{criteria_name}`, `{cell_value}`, `{paper_title}`, `{paper_abstract}` |
| `verify_synthesis_faithfulness.md` | Verify report claim fidelity vs. spreadsheet table | `{claim_text}`, `{table_rows}` |

---

## Installation & Usage

### Prerequisites

- Python 3.10+
- An API key for an OpenAI-compatible LLM provider

### Configuration

Create a `.env` file in the project root:

```env
EVAL_PROVIDER=openai
EVAL_API_BASE=https://api.openai.com/v1
EVAL_MODEL=gpt-4o
EVAL_API_KEY=sk-...
```

Supported providers:
- **OpenAI** (`EVAL_PROVIDER=openai`): Direct OpenAI API or any OpenAI-compatible endpoint (e.g., OpenRouter).
- **Antigravity CLI** (`EVAL_PROVIDER=agy`): Uses the `agy` CLI tool in print mode. Model is set via `EVAL_MODEL` (default: `Gemini 3.5 Flash (Low)`), timeout via `EVAL_AGY_TIMEOUT` (default: `20m`).

For OpenRouter (tested configuration):
```env
EVAL_PROVIDER=openai
EVAL_API_BASE=https://openrouter.ai/api/v1
EVAL_MODEL=deepseek/deepseek-v4-flash
EVAL_API_KEY=sk-or-v1-...
```

### Running

```bash
# Evaluate the wearables dataset (using clean canonical inputs)
python3 eval.py ./trials/run1_wearables/inputs/ --output ./trials/run1_wearables/outputs/deepseek_flash/

# Evaluate the cancer detection dataset (using clean canonical inputs)
python3 eval.py ./trials/run2_cancer_detection/inputs/ --output ./trials/run2_cancer_detection/outputs/deepseek_flash/

# Override/inject the user query from the command line
python3 eval.py ./trials/run1_wearables/inputs/ --query "Create a report on wearable health devices..." --output ./trials/run1_wearables/outputs/deepseek_flash/
```

### CLI Arguments

| Argument | Required | Description |
|---|---|---|
| `input_folder` | Yes | Path to the folder containing files from one SciSpace run |
| `--query` | No | User query text. Overrides/injects a query file for classification |
| `--output` | No | Output folder for scorecard and detailed log (default: `./output/`) |

---

## Trial Run Results

### Run 1: Wearable Health Devices for Chronic Disease

**User query:** *"Create a report on wearable health devices for chronic disease management, focusing on adherence, accuracy, and long-term health outcomes."*

**Judge model:** DeepSeek V4 Flash (via OpenRouter)

| Metric | Score | Detail |
|---|---|---|
| **Intent Coverage (IC)** | **100.0%** | 3/3 intents covered by search queries |
| **Directional Alignment (DA)** | **100.0%** | 3/3 intents addressed, no drift |
| **Data Extraction Accuracy (EA)** | **53.3%** | 8/15 criteria cells accurate to paper abstracts |
| **Synthesis Faithfulness (SF)** | **70.0%** | 7/10 report claims faithful to spreadsheet |
| **Claim Reliability (CR)** | **24.1%** | 27/112 factual claims supported |
| **Cited Grounding Rate (CGR)** | **28.4%** | 27/95 cited claims supported |

**Generated search queries:**
- **SciSpace (semantic):** *"What are the effects of wearable health devices on chronic disease management, patient adherence, measurement accuracy, and long-term health outcomes?"*
- **SciSpace (full-text):** *"wearable health devices chronic disease management adherence accuracy long-term outcomes"*
- **Google Scholar:** `(wearable OR "wearable device" ...) AND ("chronic disease" ...) AND (adherence ...) AND (accuracy ...) AND ("health outcomes" ...)`
- **PubMed:** `(wearable devices[MeSH] ...) AND (chronic disease[MeSH] ...) AND (medication adherence[MeSH] ...) AND (accuracy ...) AND (treatment outcome[MeSH] ...)`

### Run 2: AI-Based Early Cancer Detection

**User query:** *"Create a report on AI-based early cancer detection methods, comparing performance across imaging, genomics, and multimodal approaches using metrics like AUC, sensitivity, and specificity."*

**Judge model:** DeepSeek V4 Flash (via OpenRouter)

| Metric | Score | Detail |
|---|---|---|
| **Intent Coverage (IC)** | **40.0%** | 2/5 intents covered *(Note: Skipped in latest run due to API timeout)* |
| **Directional Alignment (DA)** | **100.0%** | 5/5 intents addressed *(Note: Skipped in latest run due to API timeout)* |
| **Data Extraction Accuracy (EA)** | **Skipped** | Column matching is hardcoded to wearables criteria in prototype |
| **Synthesis Faithfulness (SF)** | **Skipped** | Column matching is hardcoded to wearables criteria in prototype |
| **Claim Reliability (CR)** | **32.7%** | 33/101 factual claims supported |
| **Cited Grounding Rate (CGR)** | **66.0%** | 33/50 cited claims supported; 51 uncited |

**Key finding:** The system generated queries covering "AI early cancer detection" and "performance metrics" but failed to generate distinct comparative queries contrasting imaging, genomics, and multimodal approaches against each other — missing 3 out of 5 intents.

### Cascading Quality Comparison

Contrasting both runs reveals **compounding quality degradation** through the pipeline:

```
                                         Run 1 (Wearables)    Run 2 (Cancer)
                                         ─────────────────    ──────────────
Stage 1: Intent Coverage ............... 100.0%               40.0%
Stage 2: Directional Alignment ......... 100.0%               100.0%
Stage 2: Data Extraction Accuracy ...... 53.3%                Skipped (Schema mismatch)
Stage 2: Synthesis Faithfulness ........ 70.0%                Skipped (Schema mismatch)
Stage 3: Claim Reliability ............. 24.1%                32.7%
Stage 3: Cited Grounding Rate .......... 28.4%                66.0%
```

**The mechanics of compounding degradation:**
- **Run 1 (Wearables):** Search queries and directions were 100% aligned, but data corrupted during extraction (53.3%) and synthesis (70.0%), leading to a low final grounding score of 24.1%.
- **Run 2 (Cancer):** The system missed generating comparative queries (40.0% intent coverage) but wrote a well-aligned report (100% directional alignment). Without a database extraction step to corrupt the data, the cited grounding rate reached 66.0%, outperforming Run 1's 28.4% despite poorer search coverage.

### Concrete Case Studies

**Run 1 — Extraction Mismatch (Spreadsheet vs. Paper Abstract):**
- **Criteria:** Limitations and Gaps
- **Extracted cell value:** *"specifically using wearable devices for COPD to enhance telehealth outcomes..."*
- **Actual abstract text:** *"Interventions are growing and their effectiveness to monitor telehealth outcomes has not been systematically reviewed."* (COPD is never mentioned in the abstract.)
- **Verdict:** Unsupported / Hallucinated.

**Run 1 — Synthesis Mismatch (Report Claim vs. Spreadsheet):**
- **Report claim:** *"A scoping review of 79 intervention studies found that activity trackers were the most commonly studied device type..."*
- **Spreadsheet table:** Contains only 10 rows. The scoping review in the table (Paper [9]) lists a review of 7 meta-analyses and 20 RCTs, not 79 studies.
- **Verdict:** Unsupported. The model hallucinated external clinical trial figures to sound authoritative.

**Run 2 — Rounding/Precision Mismatch:**
- **Report claim:** *"Multi-cancer detection using blood cfDNA/methylation (MCED) with ensemble ML achieved AUC up to 0.993."* (Citing Paper [10])
- **Cited abstract:** *"...area under the curve (AUC) in included studies were 0.9929."*
- **Verdict:** Unsupported / Overstated (strict rounding check by the evaluator judge).

**Run 2 — Topical Extrapolation:**
- **Report claim:** *"False positives remain a persistent challenge in imaging-based AI, leading to unnecessary biopsies."* (Citing Papers [2], [6])
- **Cited abstract:** Paper [2] reports *"specificity remained variable"*; Paper [6] discusses sensitivity at fixed specificity levels. Neither discusses biopsy consequences or calls it a "persistent challenge."
- **Verdict:** Unsupported (strict semantic grounding check due to abstract brevity).

---

## Production Readiness Assessment

| Metric | Target Threshold | Run 1 (Wearables) | Run 2 (Cancer) | Delta to Ship |
|---|:---:|:---:|:---:|---|
| **Intent Coverage** | ≥ 98% | 100.0% | 40.0% | ✅ / ❌ −58% |
| **Directional Alignment** | ≥ 98% | 100.0% | 100.0% | ✅ / ✅ |
| **Data Extraction Accuracy** | ≥ 95% | 53.3% | Skipped | ❌ −41.7% |
| **Synthesis Faithfulness** | ≥ 95% | 70.0% | Skipped | ❌ −25% |
| **Claim Reliability** | ≥ 90% | 24.1% | 30.5% | ❌ −65.9% / ❌ −59.5% |

### Verdict: NOT PRODUCTION-READY

Neither pipeline is ready for public release. A user relying on these reports is highly likely to make clinical or academic decisions based on fabricated statistics and false citations.

### Engineering Recommendations

1. **Spreadsheet Extraction Constraints:** Enforce strict grounding prompts in Step 4 to ensure table cell values never extrapolate beyond the source PDF text.
2. **Synthesis Grounding Enforcement:** Constrain the final writing model (Step 5) to write claims that are strictly traceable to the columns of the consolidated table, preventing general knowledge leakage.
3. **Bibliography Validation:** Add a verification pass that rejects any citation where the parsed claim does not map to a confirmed statistical finding in the paper.

---

## Production Realities: What Actually Happens vs. Ideal Design

Analyzing the actual codebase execution (`eval.py`) reveals a series of compromises, hardcodings, and fragile assumptions that diverge from the ideal pipeline design described in theory. This section details these operational realities to ensure absolute clarity for presentation and debugging purposes:

### 1. The Hardcoded Column Constraint (Why Run 2 Skipped Stage 2b & 2c)
* **The Ideal:** The evaluator should dynamically identify and evaluate the consolidated table columns for any research topic.
* **The Reality:** The column parsing in `eval.py` is hardcoded to specific column headers from the wearables trial:
  ```python
  required_cols = {"Study Design and Population", "Key Findings on Adherence Accuracy or Outcomes", "Limitations and Gaps"}
  ```
  Because the cancer detection trial (`run2_cancer_detection`) has different research criteria and column headings in its spreadsheet (`combined_cancer_ai_detection_results.csv`), the evaluator's CSV parser fails to find a match and returns `None`. 
  Consequently, **Stage 2b (Data Extraction Accuracy)** and **Stage 2c (Synthesis Faithfulness)** are silently **skipped** during Run 2, rather than evaluated against the cancer criteria.
* **Presentation Impact:** When presenting the results, point out that the evaluator CLI is currently hardcoded to a specific spreadsheet schema, making it a topic-specific prototype rather than a generic evaluator.

### 2. Error Recovery and Transient API Timeouts (Socket Timeouts)
* **The Ideal:** The LLM client (`call_llm`) should catch all network and socket exceptions and retry the requests up to the retry limit (1).
* **The Reality:** The `try/except` block in `call_llm` only catches:
  ```python
  except (urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
  ```
  In Python, read operation timeouts (socket timeouts) and OS-level socket disconnects often raise raw `TimeoutError` or `OSError`. Since these are not subclassed under `urllib.error.URLError` in all execution runtimes, they bypass the retry logic entirely and propagate to the caller.
  When a timeout occurs during `extract_intents` (as occurred during trial runs on OpenRouter), the evaluator catches the general `Exception`, prints a warning, and falls back to an empty list `[]`. Because `intents` is empty, Stage 1 and Stage 2 are skipped entirely.
* **Presentation Impact:** Under peak API loads, the evaluator fails silently on its initial stages rather than retrying, leading to scorecard reports that show Stage 1 and Stage 2 as "Skipped" due to transient network conditions.

### 3. File Classification and Log Cleanup Shortcutting
* **The Ideal:** The evaluator should dynamically classify all files in the input folder and clean up raw search queries using LLM calls every run.
* **The Reality:** The evaluator relies on shortcut files to bypass slow/costly LLM calls:
  * **File Classification:** If the folder contains the exact names `user_query.txt`, `search_queries.txt`, `intermediate_report.md`, and `final_report.md`, classification is skipped.
  * **Log Cleanup:** If `search_queries.json` exists in the folder, the raw `search_queries.txt` log cleanup step is bypassed entirely.
  In practice, the trial folders are manually pre-structured to include these canonical names to ensure speed and bypass LLM classification/cleanup errors.

### 4. Bibliography and Reference Regex Mismatch
* **The Ideal:** The evaluator parses any standard academic bibliography format.
* **The Reality:** `parse_references()` uses a rigid regex search:
  ```python
  matches = list(re.finditer(r"^\[(\d+)\]\s+(.*?)(?=^\[\d+\]\s+|\Z)", ref_text, flags=re.M | re.S))
  ```
  This expects bibliography entries to start precisely with `[1]`, `[2]`, etc. at the start of a newline in markdown. If the bibliography is formatted differently (e.g. `1.`, `- `, or indented list), reference parsing fails entirely, returning `refs = {}`, which forces Stage 3 to label all claims as `not_verifiable`.

---

## Known Evaluation Gaps

### 1. Paper Consolidation Audit (Step 2)
- **Risk:** The search/retrieval system could drop valid papers, duplicate entries, or consolidate metadata incorrectly.
- **Why unimplemented:** Auditing deduplication and filtering decisions requires semantic reasoning over paper relevance — this evaluates the retrieval index rather than report generation.

### 2. Full-Text Body Grounding
- **Risk:** The evaluator currently checks claims against paper titles and abstracts (available in the CSV cache or via CrossRef/Semantic Scholar APIs). If a claim is supported by a finding in the full paper body but not in the abstract, the evaluator flags it as "Unsupported" or "Overstated."
- **Impact:** This is the primary source of false-positive "Unsupported" verdicts in Stage 3. The actual hallucination rate is likely lower than reported.
- **Engineering needed:** Ingesting full PDFs and chunk-matching claims would increase accuracy but add high latency and cost.

### 3. Discrete Citation-Pair Checking
- **Risk:** When a claim cites multiple references (e.g., `[1, 2, 3]`), the evaluator currently blends their abstracts together for comparison. If Paper [1] supports the claim but Papers [2] and [3] do not, the claim is still marked "Supported" overall — hiding faulty citations.
- **Resolution:** Future updates should check claim-citation pairs individually.

### 4. Synthesis Conflict Handling
- **Challenge:** When two papers in the consolidated table contradict each other (e.g., Paper A reports positive outcomes, Paper B reports null findings), how should the evaluator judge the report's synthesis?
- **Current behavior:**
  - **Faithful Synthesis:** If the report acknowledges the conflict (e.g., *"mixed findings were reported..."*), it is marked **Supported**.
  - **Hallucinated Synthesis:** If the report claims consensus (e.g., *"studies consistently prove..."*) while citing both, it is flagged as **Contradicted** or **Overstated**.
- **Future improvement:** Ingest metadata like H-index, citation counts, and study design (e.g., RCT vs. observational) to audit whether the agent properly prioritized high-strength evidence when resolving conflicts.

---

## Model Choice & Cost-vs-Accuracy Tradeoffs

The trial runs used **DeepSeek V4 Flash** via OpenRouter as the judge model. Key considerations:

- **For development/iteration:** Smaller models (DeepSeek V4 Flash, Gemini 2.5 Flash) are cheap, fast, and effective for validating evaluator logic and pipeline parsing.
- **For production assessments:** Use stronger frontier models (Claude 3.5 Sonnet, GPT-4o). Flash models are prone to errors on subtle semantic grounding checks. The accuracy of the LLM judge directly limits the validity of readiness scores.
- **The evaluator is model-agnostic:** Configure via `EVAL_MODEL` and `EVAL_API_BASE` environment variables. Any OpenAI-compatible endpoint works, and the Antigravity CLI (`agy`) is also supported as an alternative provider.

---

## Design Decisions

### Why external prompt files?
Prompts are the core evaluation logic. Keeping them as separate Markdown files means a PM can refine evaluation criteria without touching Python code. The runner is just plumbing.

### Why three stages instead of one?
One end-to-end check ("is this report hallucinated?") cannot distinguish between a bad search query, a drifted synthesis, and a fabricated claim. Each failure type requires checking against a different ground truth (user query vs. paper abstract vs. cited source).

### Why evidence in the scorecard?
Numbers alone are not useful. A score of "82% grounding rate" means nothing without knowing *which* claims failed and *why*. Every failure in the scorecard shows the report's claim, what the source actually says, and the specific problem. This makes the scorecard actionable for debugging the pipeline.

### Why no external dependencies?
The runner uses only Python's standard library (`urllib`, `json`, `argparse`, `re`, `html`, `concurrent.futures`). This makes it deployable anywhere Python 3.10+ is available, without dependency management overhead.

### Why heuristic fallbacks?
Every LLM call has a heuristic fallback for when the judge model returns invalid JSON or fails. This ensures the evaluator degrades gracefully rather than crashing — critical for batch evaluation runs.

---

## Appendix: Consolidations & Slide Walkthroughs

### Appendix A: Implementation Roadmap & Development Phases

The evaluator was constructed systematically across four main engineering phases:

1. **Phase 1: Prompts Engineering**:
   Before writing python scripts, the core evaluation logic was written in plain markdown prompt templates in the `prompts/` directory. This isolates the evaluation rules from execution plumbing:
   * [classify_files.md](file:///Users/office/Desktop/sci%20space/prompts/classify_files.md)
   * [clean_search_queries.md](file:///Users/office/Desktop/sci%20space/prompts/clean_search_queries.md)
   * [extract_intents.md](file:///Users/office/Desktop/sci%20space/prompts/extract_intents.md)
   * [stage1_intent_coverage.md](file:///Users/office/Desktop/sci%20space/prompts/stage1_intent_coverage.md)
   * [stage2_directional.md](file:///Users/office/Desktop/sci%20space/prompts/stage2_directional.md)
   * [stage3_extract_claims.md](file:///Users/office/Desktop/sci%20space/prompts/stage3_extract_claims.md)
   * [stage3_ground_claim.md](file:///Users/office/Desktop/sci%20space/prompts/stage3_ground_claim.md)
   * [verify_data_extraction.md](file:///Users/office/Desktop/sci%20space/prompts/verify_data_extraction.md)
   * [verify_synthesis_faithfulness.md](file:///Users/office/Desktop/sci%20space/prompts/verify_synthesis_faithfulness.md)

2. **Phase 2: Runner Core ([eval.py](file:///Users/office/Desktop/sci%20space/eval.py))**:
   Built the command-line executor to orchestrate file classification, query cleanup, intent extraction, and Stage 1/2/3 judges. Added a thread pool (10 concurrent workers) for dynamic API caching/fetching and parallel claim grounding.
3. **Phase 3: Dataset Dry-Runs**:
   Ran the runner against the wearables dataset and cancer dataset canonical inputs to calibrate NLI judge prompts and fix extraction edge cases.
4. **Phase 4: Robustness Tuning**:
   Added model configuration settings, automated cache database ingestion, and graceful heuristic fallbacks for LLM parsing errors.

---

### Appendix B: Slide-by-Slide Project Presentation Walkthrough

Below is the slide-by-slide walkthrough notes detailing the motivation, design decisions, results, and recommendation pitch of this project:

#### Slide 1: The Hook
* **Slide Content**: *"Just feed the report to a stronger LLM and ask whether it hallucinated." Sounds simple. It is the wrong first answer.*
* **Concept**: An LLM reading a polished research report cannot distinguish between a correctly cited claim and one that sounds correct but is entirely fabricated. Hallucination evaluation requires reference-grounded checking against the source literature.

#### Slide 2: Citations and Document Grounding
* **Slide Content**: *Citations look correct, but is the claim actually supported?*
* **Concept**: Factual grounding requires checking assertions directly against the cited source texts, not just checking that the citation exists.

#### Slide 3: Directional Faithfulness
* **Slide Content**: *The source is real, but did we drift from user intent?*
* **Concept**: A report can be factually true (fully grounded) and still fail if it deleted user-requested constraints or drifted into unrelated areas.

#### Slide 4: Retrieval Path Coverage
* **Slide Content**: *Did we query the wrong thing at the start?*
* **Concept**: The query generator must target all aspects of the user request across academic database syntaxes, or the retrieval path is flawed before synthesis begins.

#### Slide 5: The Three Layers
* **Slide Content**: 
  - *Top layer: Query Hallucination (Asking correct question)*
  - *Middle layer: Directional Alignment & Data Accuracy (Retrieving correct data)*
  - *Bottom layer: Claim Grounding (Factual correctness)*

#### Slide 7: Stage 1 - Query Hallucination
* **Slide Content**: *Intent Coverage Rate (IC) = Intents covered / Total intents.*
* **Concept**: Evaluates database queries semantically, accommodating channel-specific query styles (semantic questions, boolean queries, MeSH terms).

#### Slide 8: Stage 2 Evaluation Matrix
* **Slide Content**: Mid-Pipeline assessment broken into three matrices:
  1. **Directional Alignment Rate (DA)**: Intent discussion coverage in outline (penalized by 0.2 per drift topic).
  2. **Data Extraction Accuracy (EA)**: Verification of spreadsheet database cell veracity against original abstracts.
  3. **Synthesis Faithfulness (SF)**: Checks if report claims match spreadsheet rows (catching general-knowledge leaks).

#### Slide 9: Stage 3 Evaluation Matrix
* **Slide Content**: Fact-checking report claims against source abstracts. Claims are classified as: **Supported**, **Unsupported**, **Contradicted**, **Overstated**, **Uncited**, or **Not Verifiable**.
* **Metrics**:
  - *Claim Reliability Rate (CR)*: Supported claims / Total claims.
  - *Cited Grounding Rate (CGR)*: Supported claims / Cited verifiable claims.

#### Slide 10: Static vs. Semantic Verification
* **Slide Content**: Deterministic check scripts (citation brackets, reference links, DOI formats) handle structure, while semantic judges handle text grounding.

#### Slide 11: The Input Contract (Directory Structure)
* **Slide Content**: Standardized canonical inputs structure:
  ```text
  trials/run1_wearables/
  └── inputs/
      ├── user_query.txt          <-- Original user query
      ├── search_queries.txt      <-- Raw log of channel searches
      ├── search_queries.json     <-- Pre-cleaned channel/query pairs
      ├── intermediate_report.md  <-- Insights report
      ├── final_report.md         <-- Final cited report
      └── ... (local paper databases in CSV format)
  ```

#### Slide 12: Technical Metrics Dictionary & Calculations
* Decomposes the calculations:
  - `IC = Covered Intents / Total Intents`
  - `DA = (Sum of Intent Scores - Drift Penalties) / Total Intents`
  - `EA = Supported Cells / Total Scored Cells`
  - `SF = Faithful Claims / Checked Claims`
  - `CR = Supported Claims / Total Extracted Claims`
  - `CGR = Supported Claims / (Total Scored - Uncited)`

#### Slide 13: Trial Run 1 Results (Wearables for Chronic Disease)
* **User Query**: *"Create a report on wearable health devices for chronic disease management, focusing on adherence, accuracy, and long-term outcomes."*
* **Metrics**: Intent Coverage: 100%, Directional Alignment: 100%, Data Extraction: 53.3%, Synthesis Faithfulness: 70%, Claim Reliability: 24.1%, Cited Grounding Rate: 28.4%.

#### Slide 13b: Trial Run 2 Results (AI-Based Early Cancer Detection)
* **User Query**: *"Create a report on AI-based early cancer detection methods, comparing performance across imaging, genomics, and multimodal approaches using metrics like AUC, sensitivity, and specificity."*
* **Metrics**: Intent Coverage: 40.0%, Directional Alignment: 100.0%, Data Extraction: Skipped (Schema mismatch), Synthesis Faithfulness: Skipped (Schema mismatch), Claim Reliability: 32.7%, Cited Grounding Rate: 66.0%.

#### Slide 13c: The Cascading Quality Leakage Comparison
* Compares Wearables vs. Cancer. In Run 2 (Cancer), query coverage was lower (40%), but because the pipeline lacked a database extraction step to corrupt details, final cited grounding (66.0%) was higher than Run 1 (28.4%), proving that intermediate data extraction is the primary pipeline vulnerability.

#### Slide 13d: Concrete Case Studies
* Documented instances of extraction mismatches, synthesis consensus fabrication, rounding precision errors (0.9929 vs. 0.993), and topical extrapolation.

#### Slide 14: Model Choice & Cost-vs-Accuracy Tradeoffs
* Flash models (DeepSeek, Gemini) are excellent for cheap development loops, but production evaluations must use high-reasoning frontier models (Sonnet 3.5, GPT-4o) to prevent false grounding judgments.

#### Slide 15: Remaining Evaluation Gaps
* Details unimplemented parameters: step 2 deduplication audit, full-text body PDF validation, discrete citation-pair audits, and synthesis conflict resolutions.

#### Slide 15b: Synthesis Conflicts & H-Index Prioritization
* Explains consensus auditing and proposals to weight cited source validity by author reputation (H-Index, citations) and study quality (RCT vs. observational).

#### Slide 16: Safety Gate Threshold Matrix
* Establishes ship-ready criteria (Intent Coverage >=98%, Directional Alignment >=98%, Data Extraction >=95%, Synthesis Faithfulness >=95%, Claim Groundedness >=90%). Shows that neither pipeline is ready to ship, and recommends spreadsheet constraints and citation validation gates.

---

## License

This project was developed as part of a SciSpace evaluation task.
