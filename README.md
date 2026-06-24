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

## Evaluation Architecture

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
python eval.py ./test_input/
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
├── formatted_input/                     ← Canonical input for Run 1 (Wearables)
│   ├── user_query.txt
│   ├── search_queries.txt
│   ├── search_queries.json
│   ├── intermediate_report.md
│   └── final_report.md
│
├── test_input/                          ← Raw input for Run 1 (original messy SciSpace export)
│   ├── user_query.txt
│   ├── todo.md                          ← SciSpace planner task list
│   ├── todo.py                          ← SciSpace planner code
│   ├── sample search queries channel wise
│   ├── wearable_insights.md             ← Intermediate insights report
│   ├── wearable_health_devices_chronic_disease_report.md  ← Final report
│   ├── combined_wearable_health_chronic_disease.csv
│   ├── scispace_wearable_health_devices.csv
│   ├── scispace_fulltext_wearable_chronic.csv
│   ├── pubmed_wearable_chronic.csv
│   └── scholar_wearable_chronic_disease.csv
│
├── inputs/cancer_01/                    ← Canonical input for Run 2 (Cancer Detection)
│   ├── user_query.txt
│   ├── search_queries.txt
│   ├── search_queries.json
│   ├── intermediate_report.md
│   ├── final_report.md
│   ├── combined_cancer_ai_detection_results.csv
│   ├── scispace_cancer_detection_ai.csv
│   ├── scispace_fulltext_cancer_detection.csv
│   ├── pubmed_cancer_ai_detection.csv
│   ├── scholar_cancer_ai_detection.csv
│   └── arxiv_cancer_ai_detection.csv
│
├── output/                              ← Eval results for Run 1 (DeepSeek V4 Flash judge)
│   ├── scorecard.md
│   └── detailed_log.json
│
├── outputs/cancer_01/                   ← Eval results for Run 2 (DeepSeek V4 Flash judge)
│   ├── scorecard.md
│   └── detailed_log.json
│
├── output-openrouter-minimax/           ← Eval results for Run 1 (MiniMax judge, for comparison)
│   ├── scorecard.md
│   ├── detailed_log.json
│   ├── stdout.txt
│   └── stderr.txt
│
├── notes/                               ← Developer design notes and presentations
│   ├── 01_understanding.md              ← Process analysis of SciSpace reporting
│   ├── 02_eval_design.md                ← Mathematical design of the 3 evaluation stages
│   ├── 03_cli_sketch.md                 ← Technical design of the evaluator command-line flow
│   ├── 04_presentation.md               ← Pre-release presentation draft
│   ├── 05_plan.md                       ← Workspace roadmap and implementation phases
│   └── 06_final_presentation.md         ← Final slide-by-slide project presentation
│
└── cancer test/                         ← Raw, messy input files for Run 2 (Cancer Detection)
    ├── user query
    ├── generated queries
    ├── cancer_ai_insights.md
    ├── AI_Cancer_Detection_Report.md
    └── ... (associated source CSV files)
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
# Evaluate a SciSpace run folder
python eval.py ./test_input/

# Specify a custom output directory
python eval.py ./test_input/ --output ./my_output/

# Override/inject the user query from the command line
python eval.py ./test_input/ --query "Create a report on wearable health devices..."

# Run against the cancer detection dataset
python eval.py ./inputs/cancer_01/ --output ./outputs/cancer_01/
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
| **Intent Coverage (IC)** | **40.0%** | 2/5 intents covered |
| **Directional Alignment (DA)** | **100.0%** | 5/5 intents addressed, no drift |
| **Data Extraction Accuracy (EA)** | Skipped | No structured spreadsheet table in this run |
| **Synthesis Faithfulness (SF)** | Skipped | No spreadsheet table available |
| **Claim Reliability (CR)** | **30.5%** | 25/82 factual claims supported |
| **Cited Grounding Rate (CGR)** | **54.3%** | 25/46 cited claims supported; 36 uncited |

**Key finding:** The system generated queries covering "AI early cancer detection" and "performance metrics" but failed to generate distinct comparative queries contrasting imaging, genomics, and multimodal approaches against each other — missing 3 out of 5 intents.

### Cascading Quality Comparison

Contrasting both runs reveals **compounding quality degradation** through the pipeline:

```
                                         Run 1 (Wearables)    Run 2 (Cancer)
                                         ─────────────────    ──────────────
Stage 1: Intent Coverage ............... 100.0%               40.0%
Stage 2: Directional Alignment ......... 100.0%               100.0%
Stage 2: Data Extraction Accuracy ...... 53.3%                Skipped
Stage 2: Synthesis Faithfulness ........ 70.0%                Skipped
Stage 3: Claim Reliability ............. 24.1%                30.5%
Stage 3: Cited Grounding Rate .......... 28.4%                54.3%
```

**The mechanics of compounding degradation:**
- **Run 1 (Wearables):** Search queries and directions were 100% aligned, but data corrupted during extraction (53.3%) and synthesis (70.0%), leading to a low final grounding score of 24.1%.
- **Run 2 (Cancer):** The system missed generating comparative queries (40.0% intent coverage) but wrote a well-aligned report (100% directional alignment). Without a database extraction step to corrupt the data, the cited grounding rate reached 54.3%, outperforming Run 1's 28.4% despite poorer search coverage.

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

## License

This project was developed as part of a SciSpace evaluation task.
