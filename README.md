# SciSpace Hallucination Evaluator

> **An LLM-as-judge framework that evaluates hallucination in SciSpace's AI-powered research report-writing pipeline — from query generation to final citation grounding.**

---

## 🔍 Reviewer Audit & Verification Summary

This report serves as a self-contained, transparent record of the hallucination evaluation performed on the SciSpace pipeline outputs. **Reviewers do not need to check other folders to audit the scores or verify the claims.** The exact verbatim text instances where the evaluator flagged a hallucination are documented in the tables below.

### 1. High-Level Metrics Comparison Matrix

The evaluator was run on three configurations:
1. **Run 1: Wearables Trial (DeepSeek Flash)** - full pipeline evaluation.
2. **Run 2: Wearables Trial (MiniMax)** - claim grounding verification.
3. **Run 3: Cancer Detection Trial (DeepSeek Flash)** - claim grounding verification.

| Evaluation Metric | Run 1: Wearables (DeepSeek Flash) | Run 2: Wearables (MiniMax) | Run 3: Cancer Detection (DeepSeek Flash) | Target Ship Threshold |
| :--- | :---: | :---: | :---: | :---: |
| **Stage 1: Intent Coverage %** | **100.0% (3/3)** | **100.0% (5/5)** | *Skipped (missing logs)* | $\ge 98.0\%$ |
| **Stage 2a: Directional Alignment %** | **100.0% (3/3)** | **100.0% (5/5)** | *Skipped (missing report)* | $\ge 98.0\%$ |
| **Stage 2b: Data Extraction Accuracy %**| **53.3% (8/15)** | *Not Evaluated* | *Skipped (schema mismatch)* | $\ge 95.0\%$ |
| **Stage 2c: Synthesis Faithfulness %** | **70.0% (7/10)** | *Not Evaluated* | *Skipped (schema mismatch)* | $\ge 95.0\%$ |
| **Stage 3a: Overall Claim Reliability %** | **24.1% (27/112)** | **13.8% (4/29)** | **32.7% (33/101)** | *N/A (informational)* |
| **Stage 3b: Cited Grounding Rate %** | **28.4% (27/95)** | **13.8% (4/29)** | **66.0% (33/50)** | $\ge 90.0\%$ |

### 2. Production Release Verdict

* **Release Gate Decision:** **Do Not Ship.**
* **Rationale:** While Stage 1 intent coverage is 100%, the Stage 2 data extraction accuracy (53.3%) and Stage 3 cited grounding rate (28.4% for Run 1, 13.8% for Run 2) represent critical vulnerabilities. Over 70% of the cited facts in the wearables reports cannot be verified against the source abstracts. For high-stakes scientific or medical applications, this error rate is unsafe.

---

## Table of Contents

- [What This Is](#what-this-is)
- [Motivation](#motivation)
- [How SciSpace Generates a Report](#how-scispace-generates-a-report)
- [Three Hallucination Surfaces](#three-hallucination-surfaces)
- [Evaluation Methodology & System Design](#evaluation-methodology--system-design)
- [Metrics Dictionary](#metrics-dictionary)
- [How the Runner Works](#how-the-runner-works)
- [Project Structure](#project-structure)
- [Prompt Templates](#prompt-templates)
- [Installation & Usage](#installation--usage)
- [Trial Run Results & Detailed Evidence Tables](#trial-run-results--detailed-evidence-tables)
  - [Run 1: Wearables (DeepSeek V4 Flash)](#-run-1-wearables-deepseek-v4-flash)
  - [Run 2: Wearables (MiniMax)](#-run-2-wearables-minimax)
  - [Run 3: Cancer Detection (DeepSeek V4 Flash)](#-run-3-cancer-detection-deepseek-v4-flash)
- [Production Release Readiness Delta Analysis](#production-release-readiness-delta-analysis)
- [Production Realities: What Actually Happens vs. Ideal Design](#production-realities-what-actually-happens-vs-ideal-design)
- [Known Evaluation Gaps](#known-evaluation-gaps)
- [Model Choice & Cost-vs-Accuracy Tradeoffs](#model-choice--cost-vs-accuracy-tradeoffs)
- [Design Decisions](#design-decisions)
- [Appendices](#appendices)

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

The evaluator is a single Python script (`01_code/run_evaluator.py`, ~1,060 lines) that orchestrates the entire pipeline. It uses `urllib` for HTTP requests (no external dependencies beyond the Python standard library) and loads prompt templates from external Markdown files.

### Step 0: Classify & Clean Inputs

The runner receives a **folder** with all files from one SciSpace run. File names are not standardized — the runner infers which file is which.

```bash
python3 01_code/run_evaluator.py 03_outputs/run_1_wearables_deepseek/
```

**File classification** uses a two-tier approach:
1. **Canonical shortcut:** If the folder contains the exact canonical filenames (`user_query.txt`, `search_queries.txt`, `intermediate_report.md`, `final_report.md`), classification is skipped.
2. **LLM classification:** Otherwise, the runner reads all files, generates previews (first 500 characters each), and sends them to the LLM judge using `02_prompts/00_classify_files.md` to identify which file is the user query, search log, intermediate report, and final report.
3. **Heuristic fallback:** If the LLM returns invalid JSON, a rule-based classifier (`heuristic_classify_files()`) uses filename patterns and content markers (e.g., "Searched SciSpace", "## References") to assign roles.

**Search query cleanup** also uses a two-tier approach:
1. **Pre-cleaned JSON:** If a `search_queries.json` file exists with valid `{channel, query}` pairs, it is used directly.
2. **LLM cleanup:** Otherwise, the raw search log (which includes emoji, paper counts, status messages like "🔍 Searching scholarly literature...") is sent to the LLM using `02_prompts/01_clean_search_queries.md`.
3. **Heuristic fallback:** If the LLM fails, `heuristic_clean_search_queries()` parses `"Searched <channel>"` blocks with regex.

### Step 1: Stage 1 Eval — Query Hallucination

**LLM calls:**
1. Extract atomic intents from user query → `02_prompts/02_extract_intents.md`
2. Check search queries against intents → `02_prompts/03_stage1_intent_coverage.md`

**Deterministic computation:** Count intents covered ÷ total intents → **Intent Coverage %**

### Step 2: Stage 2 Eval — Directional Faithfulness & Data Accuracy

**LLM calls:**
1. Check intermediate report against intents + detect drift → `02_prompts/04_stage2_directional.md`
2. If a consolidated CSV with criteria columns is detected (`find_and_parse_consolidated_csv()`):
   - Verify top 5 papers' criteria cells against abstracts → `02_prompts/05_verify_data_extraction.md`
   - Verify top 10 report claims against table rows → `02_prompts/06_verify_synthesis_faithfulness.md`

**CSV detection:** The evaluator looks for CSV files containing columns matching at least 2 of: `"Study Design and Population"`, `"Key Findings on Adherence Accuracy or Outcomes"`, `"Limitations and Gaps"`. Column matching is case-insensitive with whitespace normalization.

**Deterministic computation:** Count intents addressed ÷ total intents → **Directional Alignment %**; supported cells ÷ total cells → **Data Extraction Accuracy %**; faithful claims ÷ total → **Synthesis Faithfulness %**

### Step 3: Stage 3 Eval — Claim-Level Fact-Checking

**LLM calls:**
1. Split final report into atomic claims → `02_prompts/07_stage3_extract_claims.md`
2. For each claim, judge against fetched source → `02_prompts/08_stage3_ground_claim.md`

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
├── 01_code/                             ← Code scripts and environment configurations
│   ├── run_evaluator.py                 ← The runner (~1,060 lines, zero external dependencies)
│   ├── .env.example                     ← Template for API configuration
│   └── .env                             ← Local API configuration (gitignored)
├── 02_prompts/                          ← LLM judge prompt templates (editable without touching code)
│   ├── 00_classify_files.md             ← "Identify which file is which"
│   ├── 01_clean_search_queries.md       ← "Extract channel + query pairs from messy log"
│   ├── 02_extract_intents.md            ← "Extract atomic intents from user query"
│   ├── 03_stage1_intent_coverage.md     ← "Which intents does this search query cover?"
│   ├── 04_stage2_directional.md         ← "Does this report align with these intents?"
│   ├── 05_verify_data_extraction.md     ← "Is this spreadsheet cell accurate to the paper abstract?"
│   ├── 06_verify_synthesis_faithfulness.md ← "Is this report claim faithful to the spreadsheet table?"
│   ├── 07_stage3_extract_claims.md      ← "Split report into atomic claims with citation IDs"
│   ├── 08_stage3_ground_claim.md        ← "Is this claim supported by this source?"
│   └── 09_prepare_input_folder.md       ← "Prepare canonical input folder from messy files"
│
├── 03_outputs/                          ← Evaluator trials and runs
│   ├── run_1_wearables_deepseek/        ← Trial 1: Wearables report scored by DeepSeek V4 Flash
│   │   ├── user_query.txt
│   │   ├── search_queries.txt
│   │   ├── search_queries.json
│   │   ├── intermediate_report.md
│   │   ├── final_report.md
│   │   ├── scorecard.md                 ← Output scorecard generated by the runner
│   │   ├── detailed_log.json            ← Detailed JSON results log generated by the runner
│   │   ├── combined_wearable_health_chronic_disease.csv
│   │   └── ... (other wearables CSV paper databases)
│   │
│   ├── run_2_wearables_minimax/         ← Trial 2: Wearables report scored by MiniMax
│   │   ├── user_query.txt
│   │   ├── search_queries.txt
│   │   ├── search_queries.json
│   │   ├── intermediate_report.md
│   │   ├── final_report.md
│   │   ├── scorecard.md                 ← Output scorecard generated by the runner
│   │   ├── detailed_log.json            ← Detailed JSON results log generated by the runner
│   │   ├── combined_wearable_health_chronic_disease.csv
│   │   └── ... (other wearables CSV paper databases)
│   │
│   └── run_3_cancer_detection/          ← Trial 3: AI early cancer detection report (DeepSeek)
│       ├── user_query.txt
│       ├── search_queries.txt
│       ├── search_queries.json
│       ├── intermediate_report.md
│       ├── final_report.md
│       ├── scorecard.md                 ← Output scorecard generated by the runner
│       ├── detailed_log.json            ← Detailed JSON results log generated by the runner
│       ├── combined_cancer_ai_detection_results.csv
│       └── ... (other cancer CSV paper databases)
│
├── .gitignore
└── README.md                            ← This file (contains all documentation and notes)
```

---


## Prompt Templates

All evaluation logic is driven by **external prompt templates** stored as plain Markdown files in `02_prompts/`. This makes it possible to modify evaluation criteria or update NLI rules without touching the Python runner code.

### How the Prompts Were Designed to Find Evidence

Our evaluation prompts represent a specialized **LLM-as-a-Judge** methodology designed to enforce strict semantic verification. We came up with these templates based on the following three design principles:
1. **NLI-Style Verification (Natural Language Inference):** Instead of asking the model a generic "is this hallucinated?", we force it to evaluate the assertion as a formal NLI task (verdicts of `supported`, `unsupported`, `contradicted`, or `overstated`). This bounds the model's judgment to direct text comparisons and prevents the judge from hallucinating its own reasoning.
2. **Strict Grounding Proof Constraints:** The prompts require the judge model to return a structured JSON object containing a `reason` field that must cite the exact text fragments from the source text that support or mismatch the claim.
3. **Information Siloing:** The prompts isolate the context. For instance, Stage 3 fact-checking provides the model *only* with the specific cited paper abstract text and the specific claim text, preventing general knowledge leakage.

Here are the details of the prompts used by the evaluator:

| Prompt File | Evaluation Surface | Inputs Ground Truth | Target Assertions | JSON Schema |
|---|---|---|---|---|
| [00_classify_files.md](file:///Users/office/Desktop/sci%20space/02_prompts/00_classify_files.md) | Pipeline Pre-check | Filename patterns | Classifier labels | `{"user_query": "...", ...}` |
| [01_clean_search_queries.md](file:///Users/office/Desktop/sci%20space/02_prompts/01_clean_search_queries.md) | Search Query Prep | Raw text query log | Cleaned search query list | `{"queries": [{"channel": "...", "query": "..."}]}` |
| [02_extract_intents.md](file:///Users/office/Desktop/sci%20space/02_prompts/02_extract_intents.md) | Intent Extraction | User Query | Atomic Intents List | `{"intents": ["...", "..."]}` |
| [03_stage1_intent_coverage.md](file:///Users/office/Desktop/sci%20space/02_prompts/03_stage1_intent_coverage.md) | Stage 1 (Search Coverage) | User Intents list | Search queries list | `{"intents": [{"intent": "...", "covered": true, "reason": "..."}]}` |
| [04_stage2_directional.md](file:///Users/office/Desktop/sci%20space/02_prompts/02_prompts/04_stage2_directional.md) | Stage 2a (Alignment) | User Intents list | Report section outline | `{"intents": [{"intent": "...", "status": "addressed", ...}], "drift": []}` |
| [05_verify_data_extraction.md](file:///Users/office/Desktop/sci%20space/02_prompts/05_verify_data_extraction.md) | Stage 2b (Spreadsheet Audit) | Paper Abstract verbatim | Table cell values | `{"verdict": "supported", "reason": "..."}` |
| [06_verify_synthesis_faithfulness.md](file:///Users/office/Desktop/sci%20space/02_prompts/06_verify_synthesis_faithfulness.md) | Stage 2c (Synthesis Faith) | Spreadsheet rows | Synthesis report claims | `{"verdict": "supported", "reason": "..."}` |
| [07_stage3_extract_claims.md](file:///Users/office/Desktop/sci%20space/02_prompts/07_stage3_extract_claims.md) | Stage 3 Preparation | Final Report text | Factual statements list | `{"claims": ["...", "..."]}` |
| [08_stage3_ground_claim.md](file:///Users/office/Desktop/sci%20space/02_prompts/08_stage3_ground_claim.md) | Stage 3 (Claim Grounding) | Verbatim Cited Abstract | Report Claim | `{"verdict": "supported", "reason": "...", "source_says": "..."}` |

The exact prompt code for the verification stages (`verify_data_extraction.md`, `verify_synthesis_faithfulness.md`, and `stage3_ground_claim.md`) can be examined inside the [02_prompts/](file:///Users/office/Desktop/sci%20space/02_prompts/) directory.


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
# Evaluate the wearables DeepSeek run (writes scorecard.md and detailed_log.json to the folder)
python3 01_code/run_evaluator.py 03_runs/run_1_wearables_deepseek/ --output 04_evals/run_1_wearables_deepseek/

# Evaluate the wearables MiniMax run
python3 01_code/run_evaluator.py 03_runs/run_2_wearables_minimax/ --output 04_evals/run_2_wearables_minimax/

# Evaluate the cancer detection run
python3 01_code/run_evaluator.py 03_runs/run_3_cancer_detection/ --output 04_evals/run_3_cancer_detection/

# Override/inject the user query from the command line
python3 01_code/run_evaluator.py 03_runs/run_1_wearables_deepseek/ --query "Create a report on wearable health devices..." --output 04_evals/run_1_wearables_deepseek/
```

*Note: The CLI writes to `scorecard.md` and `detailed_log.json` inside the specified output folder.*

### CLI Arguments

| Argument | Required | Description |
|---|---|---|
| `input_folder` | Yes | Path to the folder containing files from one SciSpace run |
| `--query` | No | User query text. Overrides/injects a query file for classification |
| `--output` | No | Output folder for scorecard and detailed log (default: `./output/`) |

---


## Trial Run Results & Detailed Evidence Tables

This section documents the detailed evaluation results for each of the three runs. Below are the complete evidence logs showing how each metric is traceably computed based on verbatim comparisons between the report text and source evidence.

#### 📊 Run 1: Wearables (DeepSeek V4 Flash)

##### Stage 1: Search Query Intent Coverage Evidence Table
Methodology: Verifies if the user intents are addressed by generated queries. Prompt: `02_prompts/03_stage1_intent_coverage.md`.

| User Intent | Coverage Status | Coverage Proof / Reason |
| :--- | :---: | :--- |
| Adherence to wearable health devices for chronic disease management | ✅ Covered | All four queries explicitly mention adherence or related terms (patient compliance/medication adherence), covering this intent. |
| Accuracy of wearable health devices for chronic disease management | ✅ Covered | All four queries include accuracy or validity/reliability terms, covering this intent. |
| Long-term health outcomes from wearable health devices for chronic disease management | ✅ Covered | All four queries explicitly mention long-term outcomes, health outcomes, or clinical outcomes, covering this intent. |


##### Stage 2a: Directional Alignment Evidence Table
Methodology: Verifies if the user intents are addressed in the report outline without topic drift. Prompt: `02_prompts/04_stage2_directional.md`.

| User Intent / Topic | Alignment Status | Section-Level Mapping / Evidence |
| :--- | :---: | :--- |
| Adherence to wearable health devices for chronic disease management | ✅ Aligned | The report includes a dedicated 'Patient adherence' section discussing facilitators, barriers, and correlates of adherence. |
| Accuracy of wearable health devices for chronic disease management | ✅ Aligned | The report has a 'Sensor accuracy' section with a table summarizing accuracy evidence for activity, glucose, heart rate, and blood pressure. |
| Long-term health outcomes from wearable health devices for chronic disease management | ✅ Aligned | The report contains a 'Long-term outcomes' section covering diabetes, cardiovascular disease, hypertension, heart failure, and COPD with evidence synthesis. |


##### Stage 2b: Data Extraction Accuracy Evidence Table
Methodology: Audits intermediate spreadsheet values against source abstract text. Prompt: `02_prompts/05_verify_data_extraction.md`.

| Paper Title | Criteria Column | Extracted Cell Value (Awaiting Verification) | Verdict | Evaluator Verification Detail (Exact Text Contrast) |
| :--- | :--- | :--- | :---: | :--- |
| Clinical Effectiveness of Wearable Technologies in Chronic Disease Management: Evidence from CaseBased Evaluation and Real-World Applications | Study Design and Population | The study evaluates clinical outcomes and patient adherence through case-based evaluation and real-world applications. It specifically includes hypertension management using wearable fitness trackers. | ✅ Supported | The abstract mentions hypertension-focused wearables, monitoring disease, and reporting usage rates and compliance, which aligns with the cell value's claim of evaluating clinical outcomes and patient adherence through case-based evaluation and real-world applications, specifically including hypertension management using wearable fitness trackers. |
| Clinical Effectiveness of Wearable Technologies in Chronic Disease Management: Evidence from CaseBased Evaluation and Real-World Applications | Key Findings on Adherence Accuracy or Outcomes | The work evaluates clinical outcomes and patient adherence related to wearable technologies. It reports on usage rates and compliance, and validates sensor readings against standards. However, outcome data span limited follow-up rather than multi-year results. The paper also addresses device accuracy and data reliability, using hypertension management as a case study with wearable fitness trackers. | ✅ Supported | The abstract explicitly states that the paper uses hypertension-focused wearables, reports usage rates and compliance, validates sensor readings against standards, and notes that outcome data span limited follow-up rather than multi-year results. The cell value matches all these points, including the case study on hypertension management and wearable fitness trackers. |
| Clinical Effectiveness of Wearable Technologies in Chronic Disease Management: Evidence from CaseBased Evaluation and Real-World Applications | Limitations and Gaps | Outcome data span limited follow-up rather than multi-year results. The work evaluates clinical outcomes, patient adherence, and issues related to device accuracy, data reliability, and integration. | ❌ Overstated | The abstract directly supports the 'limited follow-up' claim, but the cell value asserts evaluation of 'clinical outcomes' and 'integration', which are not explicitly stated in the abstract; only compliance and sensor validation are mentioned. |
| The use of wearable devices in chronic disease management to enhance adherence and improve telehealth outcomes: A systematic review and meta-analysis. | Study Design and Population | This paper is a systematic review and meta-analysis. It focuses on chronic disease management, specifically using wearable devices for COPD to enhance telehealth outcomes, and for people with DM (Diabetes Mellitus) and CD (Chronic Disease) with educational support. | ❌ Unsupported | The abstract does not mention specific conditions such as COPD, Diabetes Mellitus, or Chronic Disease with educational support. It only generally discusses wearable devices in chronic disease management and telehealth outcomes. The title confirms it is a systematic review and meta-analysis, but the cell value includes details not present in the provided abstract. |
| The use of wearable devices in chronic disease management to enhance adherence and improve telehealth outcomes: A systematic review and meta-analysis. | Key Findings on Adherence Accuracy or Outcomes | Evidence supports the use of wearable devices (WD) for COPD to enhance telehealth outcomes for disease management. For individuals with diabetes mellitus (DM) and chronic disease (CD), WD with educational support can enhance support beyond usual care. The paper focuses on the effectiveness of these technologies to monitor telehealth outcomes. | ❌ Unsupported | The abstract only mentions that wearable device interventions are growing and that the effectiveness to monitor telehealth outcomes has not been fully assessed. It provides no specific evidence or findings regarding COPD, diabetes mellitus, chronic disease with educational support, or enhanced telehealth outcomes as claimed in the cell value. |
| The use of wearable devices in chronic disease management to enhance adherence and improve telehealth outcomes: A systematic review and meta-analysis. | Limitations and Gaps | The metadata indicates that the effectiveness of wearable devices to monitor telehealth outcomes has not been systematically reviewed. The tldr suggests evidence supports wearable devices for COPD to enhance telehealth outcomes and for DM and CD with educational support, implying a potential gap in broader applications or without educational support. | ❌ Overstated | The abstract only states that 'the effectiveness of these technologies to monitor telehealth outcomes has not been systematically reviewed,' which supports the first part of the cell value. However, the cell value further claims specific evidence for COPD, DM, and CD with educational support, which is not mentioned in the abstract. This additional detail goes beyond what the abstract provides, making the cell value overstated. |
| Wearable Devices in Remote Cardiac Rehabilitation With and Without Weekly Online Coaching for Patients With Coronary Artery Disease: Randomized Controlled Trial. | Study Design and Population | The study design is a Randomized Controlled Trial. The target population is patients with Coronary Artery Disease, specifically focusing on remote cardiac rehabilitation. | ✅ Supported | The paper title explicitly states 'Randomized Controlled Trial' and 'Patients With Coronary Artery Disease' focusing on 'Remote Cardiac Rehabilitation', matching the cell value exactly. |
| Wearable Devices in Remote Cardiac Rehabilitation With and Without Weekly Online Coaching for Patients With Coronary Artery Disease: Randomized Controlled Trial. | Key Findings on Adherence Accuracy or Outcomes | The abstract states that wearable devices and real-time monitoring offer a potential solution to enhance adherence to remote cardiac rehabilitation programs and their outcomes. The relevance metadata indicates "Adherence assessment: Highly Relevant" and "Long-term health outcomes: Highly Relevant." However, specific quantitative results for adherence, sensor accuracy, or long-term outcomes are not detailed in the abstract or other provided metadata fields. The paper does not evaluate sensor accuracy. | ✅ Supported | The abstract explicitly states that 'The integration of wearable devices and real-time monitoring offers a potential solution to enhance adherence to remote CR programs and their outcomes,' which matches the cell value's claim. The cell value also correctly notes the absence of specific quantitative results and sensor accuracy evaluation, which is consistent with the abstract's lack of such details. |
| Wearable Devices in Remote Cardiac Rehabilitation With and Without Weekly Online Coaching for Patients With Coronary Artery Disease: Randomized Controlled Trial. | Limitations and Gaps | The abstract notes that participation in cardiac rehabilitation programs remains limited due to associated challenges. The paper's relevance metadata indicates it "does not evaluate sensor accuracy," highlighting a device validation issue. | ❌ Unsupported | The abstract supports the first part about limited participation in cardiac rehabilitation, but it does not mention anything about sensor accuracy or device validation issues. The claim that the paper 'does not evaluate sensor accuracy' is not present in the abstract. |
| Wearable Tech and Chronic Disease Management: An Interdisciplinary Study of Bioengineering, Data Analytics, and Patient Psychology | Study Design and Population | The study involved watching 150 patients with chronic illnesses for six months using special wearable devices. This observational approach included processing physical and blood level data, activity, and medication use. The study focused on managing diabetes, cardiovascular disease, and other illnesses. | ✅ Supported | The abstract states 'Analysis of data from 150 patients' and mentions managing diabetes, cardiovascular disease, and other illnesses, which matches the cell value's description of 150 patients with chronic illnesses and the focus on these conditions. The abstract also discusses wearable devices for monitoring health, aligning with the cell value's mention of special wearable devices and processing physical and blood level data, activity, and medication use. |
| Wearable Tech and Chronic Disease Management: An Interdisciplinary Study of Bioengineering, Data Analytics, and Patient Psychology | Key Findings on Adherence Accuracy or Outcomes | Analysis of data from 150 patients found that using wearables led to better symptom management, more compliance with medications, and fewer hospital visits. Wearables helped accurately record symptoms, cutting hospital admissions by 20%. People using simple devices felt more capable and interested in managing their health. However, psychological resistance due to privacy concerns and feeling constantly watched was noted. | ❌ Overstated | The abstract supports the general findings that wearables led to better symptom management, medication compliance, and fewer hospital visits, and mentions privacy concerns. However, the cell value adds specific details not present in the abstract: a 20% reduction in hospital admissions, reference to 'simple devices', and a statement about patients feeling 'more capable and interested' in managing their health. These exaggerations make the cell value overstated. |
| Wearable Tech and Chronic Disease Management: An Interdisciplinary Study of Bioengineering, Data Analytics, and Patient Psychology | Limitations and Gaps | The study's limitations include a modest sample size, hindering generalizability, and limited statistical analysis. Its short duration might not reveal long-term psychological phenomena. Results could be biased due to participant self-reporting. Challenges also arise from integrating diverse devices and software, and concerns about error in methods used. | ❌ Unsupported | The abstract does not mention limitations such as modest sample size, limited statistical analysis, short duration, self-reporting bias, or integration challenges. Instead, it reports positive findings from 150 patients and mentions privacy, usability, and mental barriers as areas needing attention, but not these specific limitations. |
| IOT-Enabled Smart Healthcare: Developing Predictive Models for Chronic Disease Management Using Wearable Sensors | Study Design and Population | The study utilized a mixed-methods research approach, combining quantitative data from performance measurements, real-time monitoring, and cost analyses with qualitative information from surveys. The target population included 200 chronic disease patients and 50 healthcare professionals, focusing on chronic disease management. | ✅ Supported | The abstract explicitly states that the study used a mixed-methods approach combining quantitative data (performance measurements, real-time monitoring, cost analyses) and qualitative information from surveys, and that the target population included 200 chronic disease patients and 50 healthcare professionals, focusing on chronic disease management. |
| IOT-Enabled Smart Healthcare: Developing Predictive Models for Chronic Disease Management Using Wearable Sensors | Key Findings on Adherence Accuracy or Outcomes | Predictive models, particularly Neural Networks, achieved 92.4% accuracy in identifying chronic illness cases. Real-time monitoring led to a 50% reduction in hospital admissions for respiratory disease patients. Patient satisfaction was 9.0 out of 10, and overall annual cost reduction was 43.3%. The average user utilized the system three times a day, increasing patient-provider interactions by 150%. | ✅ Supported | The abstract explicitly states all numerical values found in the cell value: predictive models (Neural Network) achieved 92.4% accuracy, patient satisfaction of 9.0 out of 10, 50% reduction in hospital admissions for respiratory disease, 43.3% annual cost reduction, average usage three times a day, and 150% increase in patient-provider interactions. |
| IOT-Enabled Smart Healthcare: Developing Predictive Models for Chronic Disease Management Using Wearable Sensors | Limitations and Gaps | Not available in metadata. | ✅ Supported | The abstract does not mention any limitations or gaps, so the cell value 'Not available in metadata' accurately reflects the absence of such information in the provided text. |


##### Stage 2c: Synthesis Faithfulness Evidence Table
Methodology: Verifies if synthesized report claims are faithful to the spreadsheet rows. Prompt: `02_prompts/06_verify_synthesis_faithfulness.md`.

| Report Claim | Synthesis Verdict | Evaluator Verification Detail (Table Context Check) |
| :--- | :---: | :--- |
| The evidence base remains heterogeneous, with significant variation in study designs, device types, target populations, and outcome measures. | ✅ Faithful | Multiple papers document heterogeneity: Paper [1] uses case-based evaluation and real-world applications; Paper [2] is a systematic review and meta-analysis; Paper [3] is an RCT; Paper [4] is an observational study; Paper [5] uses mixed methods; Paper [6] explores effectiveness; Paper [7] is a data-driven observational study; Papers [8], [9], and [10] are systematic reviews. The table also shows variation in device types (fitness trackers, smartwatches, IoT sensors), target populations (hypertension, COPD, diabetes, coronary artery disease, lifestyle diseases), and outcome measures (adherence, clinical outcomes, sensor accuracy, cost savings, patient satisfaction). |
| This report draws on a comprehensive literature search that identified 93 relevant studies. | ✅ Faithful | The table includes 10 papers, each describing a study on wearable technologies in chronic disease management. The claim that the report draws on a comprehensive literature search that identified 93 relevant studies is supported by the presence of multiple papers, though the exact count of 93 is not directly verifiable from the table. However, the table rows collectively represent a substantial body of literature consistent with a comprehensive search. |
| Wearable health devices leverage advances in miniaturized sensors, wireless connectivity, and data analytics to capture physiological signals such as heart rate, physical activity, glucose levels, and blood pressure in ambulatory settings. | ✅ Faithful | Multiple papers provide evidence for the claim. Paper [1] validates sensor readings for hypertension management, implying blood pressure monitoring. Paper [7] mentions blood glucose fluctuation and uses high-frequency physiological measurements. Paper [9] reports step count (physical activity) and glucose monitoring via CGM. Wireless connectivity and data analytics are inherent in IoT-enabled studies (Papers [5], [7]) and real-time monitoring approaches. These collectively show that wearable health devices leverage miniaturized sensors, wireless connectivity, and data analytics to capture heart rate, physical activity, glucose levels, and blood pressure in ambulatory settings. |
| Continuous monitoring provides richer, more granular data than episodic clinical assessments, potentially enabling earlier detection of disease exacerbations and more precise titration of therapies. | ✅ Faithful | Multiple papers (e.g., Papers [4], [5], [7], [9]) document that continuous monitoring via wearables leads to improved outcomes such as earlier detection of deterioration, reduced hospital admissions, and better symptom management, which aligns with the claim that continuous monitoring provides richer, more granular data enabling earlier detection and precise therapy titration. |
| Real-time feedback and visualization of health data may enhance patient self-awareness and motivation, supporting behavior change through mechanisms described in self-regulation theory and the health belief model. | ❌ Unsupported | No row in the table mentions self-regulation theory, the health belief model, or explicitly describes real-time feedback/visualization enhancing self-awareness and motivation through those theoretical mechanisms. The papers discuss adherence, behavior change, and outcomes but lack the specific theoretical framing in the claim. |
| Remote monitoring capabilities facilitate telehealth interventions, reducing barriers to care access and enabling more frequent clinician-patient interactions without the burden of in-person visits. | ✅ Faithful | Paper [5] explicitly states that real-time monitoring led to a 50% reduction in hospital admissions (reducing barriers to care access) and increased patient-provider interactions by 150% (enabling more frequent clinician-patient interactions without in-person visits). This directly supports the claim. |
| Device accuracy varies widely across manufacturers and use contexts, with many consumer devices lacking rigorous clinical validation. | ✅ Faithful | Paper 7 highlights 'device heterogeneity affecting data accuracy and interoperability,' supporting variability across manufacturers and use contexts. Papers 1, 3, 10, and others note that many devices lack rigorous clinical validation (e.g., Paper 3 'does not evaluate sensor accuracy,' Paper 10 notes 'minimal evidence for long-term health outcomes' and focus on device technology rather than clinical outcomes, Paper 1 mentions limited follow-up and issues with accuracy and data reliability). Thus, the table entries collectively support the claim. |
| Patient adherence to wearable devices often declines over time, driven by factors including device discomfort, data privacy concerns, and waning motivation. | ✅ Faithful | Multiple papers in the table document factors that drive declining adherence. Paper [4] notes 'psychological resistance due to privacy concerns and feeling constantly watched' (data privacy concerns). Paper [9] lists 'user fatigue leading to low long-term adherence' (waning motivation). Paper [1] and others mention device accuracy and reliability issues, which relate to device discomfort. Paper [7] shows adherence declines with age, and Paper [6] discusses how device design influences long-term use. Thus, the claim that adherence declines over time due to discomfort, privacy concerns, and waning motivation is supported by the table. |
| The integration of wearable-generated data into clinical workflows remains limited, with issues of data standardization, interoperability, and clinician time constraints hindering effective use. | ❌ Overstated | The claim includes 'clinician time constraints' as a hindrance, but none of the table rows mention this issue. While papers [4], [7], and [9] discuss interoperability and paper [9] mentions lack of standardization, the specific element of clinician time constraints is absent, making the claim stronger than the documented evidence. |
| A scoping review of 79 intervention studies found that activity trackers were the most commonly studied device type, used in 53% of studies, with diabetes as the most frequent target condition, appearing in 23% of studies. | ❌ Unsupported | The claim states a scoping review of 79 intervention studies found activity trackers were the most commonly studied device type (53% of studies) and diabetes the most frequent target condition (23% of studies). None of the table rows mention a scoping review with 79 studies, nor do they provide these specific percentages or rankings. Paper [9] is a scoping review but of 7 meta-analyses and 20 RCTs, not 79 intervention studies, and does not report those statistics. |


##### Stage 3: Cited Claim Grounding Evidence Tables
Methodology: Extracts report claims and grounds them against cited papers. Prompt: `02_prompts/08_stage3_ground_claim.md`.

###### Table 3a: Factual Hallucinations (Unsupported, Overstated, or Contradicted Claims)
| Report Claim | Citations | Verdict | Source Paper Says (Verbatim Abstract) | Contrast Evidence / Hallucination Detail |
| :--- | :--- | :---: | :--- | :--- |
| The evidence base remains heterogeneous, with significant variation in study designs, device types, target populations, and outcome measures. | [3], [4] | UNSUPPORTED | Source 3 describes a specific randomized controlled trial on wearable devices in cardiac rehabilitation; Source 4 discusses an interdisciplinary study on wearable tech and chronic disease management, but neither addresses heterogeneity of the evidence base. | Neither source discusses the evidence base as being heterogeneous or mentions variation in study designs, device types, target populations, or outcome measures. |
| Wearable health devices leverage advances in miniaturized sensors, wireless connectivity, and data analytics to capture physiological signals such as heart rate, physical activity, glucose levels, and blood pressure in ambulatory settings. | [7], [8] | UNSUPPORTED | The source focuses on wrist-worn activity trackers and their impact on health outcomes, not on the underlying technology or specific physiological signals like glucose and blood pressure. | The source discusses wrist-worn wearables for physical activity and cardiometabolic outcomes but does not mention miniaturized sensors, wireless connectivity, data analytics, or the specific capture of glucose levels and blood pressure in ambulatory settings. |
| Real-time feedback and visualization of health data may enhance patient self-awareness and motivation, supporting behavior change through mechanisms described in self-regulation theory and the health belief model. | [11] | UNSUPPORTED | The integration of wearable devices and real-time monitoring offers a potential solution to enhance adherence to remote CR programs and their outcomes. | The source mentions that real-time monitoring may enhance adherence to remote cardiac rehabilitation, but it does not discuss self-awareness, motivation, or the specific theories (self-regulation theory, health belief model) mentioned in the claim. |
| Remote monitoring capabilities facilitate telehealth interventions, reducing barriers to care access and enabling more frequent clinician-patient interactions without the burden of in-person visits. | [2], [12] | UNSUPPORTED | Wearable technology enables continuous monitoring, early detection, and personalized care in heart failure management. | The source texts discuss wearable devices for continuous monitoring and early detection but do not mention reducing barriers to care access or enabling more frequent clinician-patient interactions without in-person visits. |
| Device accuracy varies widely across manufacturers and use contexts, with many consumer devices lacking rigorous clinical validation. | [13], [14] | UNSUPPORTED | The provided source texts are titles only and contain no information about device accuracy or clinical validation. | The source texts do not mention device accuracy varying across manufacturers and use contexts or lack of clinical validation for consumer devices. |
| Patient adherence to wearable devices often declines over time, driven by factors including device discomfort, data privacy concerns, and waning motivation. | [15], [16] | UNSUPPORTED | First source: focuses on scoping review of wearables for chronic disease self-management, outcomes, and types; second source: mentions therapeutic adherence and quality of life but not decline or specific factors. | Neither source discusses patient adherence declining over time or the specific drivers mentioned (device discomfort, data privacy concerns, waning motivation). |
| These reviews consistently note significant heterogeneity in study populations, intervention components, outcome measures, and follow-up duration. | [2], [3], [4], [5], [6] | UNSUPPORTED | The closest mention is from citation 5, which notes a mean age range and mixed results, but it does not explicitly discuss heterogeneity in the four listed aspects. | None of the provided source texts state or clearly imply significant heterogeneity in study populations, intervention components, outcome measures, and follow-up duration. |
| Meta-analytic approaches have been applied where sufficient homogeneity exists, particularly for continuous glucose monitoring in diabetes and physical activity interventions in cardiovascular disease. | [6], [27] | UNSUPPORTED | The source summarizes an umbrella review of wrist-worn wearables focusing on physical activity and cardiometabolic outcomes, but does not discuss continuous glucose monitoring or specific disease-based meta-analyses. | The source text does not mention meta-analytic approaches applied to continuous glucose monitoring in diabetes or physical activity interventions in cardiovascular disease. |
| These trials typically compare wearable-based interventions against usual care or attention-control conditions, with follow-up periods ranging from weeks to months, though few extend beyond one year. | [1], [5] | UNSUPPORTED | The source states it included 'randomised and observational studies' with a publication date range of January 1st 2016 – July 1st 2021, but does not specify comparison conditions or follow-up periods. | The source does not describe the design of trials (e.g., comparison groups or follow-up durations) for wearable-based interventions; it only reports on the types of studies included and their outcomes. |
| Validation evidence is strongest for activity tracking and continuous glucose monitoring, but remains limited for emerging technologies such as cuffless blood pressure monitors. | [13], [14], [27] | UNSUPPORTED | The source reviews evidence for wrist-worn wearables (activity trackers) and notes limited/inconsistent effects on cardiometabolic risk markers, but does not address continuous glucose monitoring or cuffless blood pressure monitors. | The source text discusses wrist-worn wearables and activity tracking, but does not mention continuous glucose monitoring, cuffless blood pressure monitors, or compare validation evidence across these technologies. |
| A scoping review of 79 intervention studies found that while many studies reported short-term benefits, long-term adherence and sustained outcome effects were mixed. | [15] | UNSUPPORTED | The scoping review identifies and describes chronic diseases, wearable devices, and health outcomes assessed in 79 intervention studies, but does not discuss adherence or effect durations. | The source does not mention short-term benefits, long-term adherence, or sustained outcome effects; it only describes the types of studies and outcomes reported. |
| In a longitudinal study of 184 patients with axial spondyloarthritis using a smartphone-based self-tracking app, six factors explained 27% of the variance in adherence: age, device type, timing of interactions, and reported symptom severity. | [30] | UNSUPPORTED | We identify six significant correlates of self-tracking adherence... adherence correlates with the age of the user, the types of tracking devices, preferences for types of data to record, the timing of interactions, and the reported symptom severity. | The source does not mention that the six factors explained 27% of the variance in adherence; it only lists six correlates without any variance percentage. |
| Older users demonstrated higher adherence to manual self-tracking. | [30] | UNSUPPORTED | Our data provides evidence that adherence correlates with the age of the user. | The source states that adherence correlates with user age but does not specify the direction (higher or lower) for older users. |
| Users tracked more consistently when the device measured symptoms or behaviors perceived as directly relevant to their condition. | [15], [30] | UNSUPPORTED | adherence correlates with ... preferences for types of data to record | The source discusses correlates of adherence including preferences for types of data to record, but does not state that users tracked more consistently when the device measured symptoms or behaviors perceived as directly relevant to their condition. |
| Even passive devices face adherence challenges related to comfort, battery life, and the need for regular charging and syncing. | [1], [15] | UNSUPPORTED | The source discusses wearable devices for chronic disease self-management but does not address adherence challenges for passive devices. | The source does not mention adherence challenges related to comfort, battery life, or the need for regular charging and syncing for passive devices. |
| Real-time feedback, reminders, and coaching are consistently associated with better adherence and improved telehealth outcomes. | [2], [3] | UNSUPPORTED | The second abstract says 'The integration of wearable devices and real-time monitoring offers a potential solution to enhance adherence to remote CR programs and their outcomes.' The first abstract mentions evaluating the effectiveness of wearable devices to monitor telehealth outcomes but does not specify feedback, reminders, or coaching. | The provided abstracts mention real-time monitoring as a potential solution but do not state that real-time feedback, reminders, and coaching are consistently associated with better adherence and improved telehealth outcomes. |
| An RCT of remote cardiac rehabilitation for coronary artery disease patients found that wearable devices combined with weekly online coaching enhanced adherence to rehabilitation programs. | [3] | OVERSTATED | The integration of wearable devices and real-time monitoring offers a potential solution to enhance adherence to remote CR programs and their outcomes. | The source only describes wearable devices and real-time monitoring as a 'potential solution' to enhance adherence, not a definitive finding of enhanced adherence from combining wearables with weekly online coaching. |
| When wearable data are reviewed by healthcare providers and incorporated into treatment decisions, patients perceive greater value and relevance, supporting sustained use. | [1], [17] | UNSUPPORTED | The source discusses wearable technology for monitoring health metrics, patient compliance, and integration challenges, but does not address provider review or treatment decisions. | The source does not mention healthcare providers reviewing wearable data, incorporating it into treatment decisions, or patients perceiving greater value and relevance leading to sustained use. |
| User-centered design features, including intuitive interfaces, comfortable form factors, and aesthetically appealing designs, support adherence, though these factors are less frequently studied in clinical research. | [15], [19] | UNSUPPORTED | The source focuses on wearable devices for chronic disease self-management, listing outcomes like clinical, behavioral, and patient technology experience, but does not address user-centered design features or their study frequency. | The provided source text does not mention user-centered design features, intuitive interfaces, comfortable form factors, aesthetically appealing designs, or their relation to adherence, nor does it discuss how frequently these factors are studied. |
| Usability and comfort issues such as device ease of use, battery life, and physical comfort limit sustained wear. | [1], [15] | UNSUPPORTED | The source focuses on the range of chronic diseases and wearable devices used, and mentions 'patient technology experience' as an outcome category, but does not address specific usability or comfort limitations. | The source does not discuss usability, comfort issues, battery life, or physical comfort limiting sustained wear. |
| Measurement fatigue—declining motivation to track health behaviors over time—is a well-documented phenomenon. | [15], [16] | UNSUPPORTED | Sources discuss wearable devices for chronic disease self-management and quality of life, but do not address measurement fatigue. | Neither source text mentions 'measurement fatigue' or declining motivation to track health behaviors. |
| Trials and meta-analyses report a weighted mean difference of approximately +1,519 steps per day when wearables are used in behavioral interventions compared to control conditions. | [6] | UNSUPPORTED | The abstract discusses wearable device interventions in chronic disease management but provides no data on step counts. | The source abstract does not mention any specific numerical result such as a weighted mean difference in steps per day. |
| Research-grade accelerometers generally show higher accuracy than consumer devices, but many consumer trackers demonstrate acceptable validity for population-level research and clinical applications focused on relative changes. | [7], [27] | UNSUPPORTED | The source focuses on the effectiveness of interventions using wrist-worn wearables and does not compare device accuracy or validity. | The source does not discuss the accuracy of research-grade accelerometers versus consumer devices, nor does it mention the validity of consumer trackers for population-level research or clinical applications. |
| Accuracy varies by activity type, with most devices performing better for walking and running than for cycling, swimming, or resistance training. | [7] | UNSUPPORTED | The source discusses wrist-worn wearables' impact on physical activity, cardiometabolic risk markers, quality of life, etc., but never mentions accuracy for different activities. | The source does not discuss accuracy of devices by activity type; it focuses on health outcomes and effectiveness of interventions. |
| A meta-analysis of 15 RCTs involving 2,461 patients found that CGM use reduced HbA1c by a weighted mean difference of −0.17% and increased time-in-range by approximately 70.7 minutes per day. | [6] | UNSUPPORTED | Wearable device (WD) interventions are rapidly growing in chronic disease management; nevertheless, the effectiveness of these technologies to monitor telehealth outcomes has not been a... | The provided source text only mentions wearable device interventions in chronic disease management and does not report any specific meta-analysis results about CGM, HbA1c reduction, or time-in-range. |
| Modest improvements in glycemic control reduce the risk of microvascular complications such as retinopathy, nephropathy, and neuropathy. | [6], [8] | UNSUPPORTED | The source focuses on the effectiveness of wearable device interventions and smartwatch technology, not on glycemic control and microvascular risk reduction. | The provided source text discusses wearable devices and smartwatch technology for diabetes management but does not mention the relationship between glycemic control and microvascular complications. |
| CGM limitation: lag time between interstitial and blood glucose levels is typically 5-15 minutes. | [8] | UNSUPPORTED | Only the title and authors of reference [8] are provided. | The provided source text only lists the citation details and does not contain any information about lag time between interstitial and blood glucose levels. |
| CGM is considered standard of care for many patients with type 1 diabetes and is increasingly used in type 2 diabetes management. | [6], [8] | UNSUPPORTED | The role of smartwatch technology in the provision of care for type 1 or 2 diabetes or gestational diabetes: systematic review. | The source text for reference [8] discusses smartwatch technology in diabetes care but does not mention CGM or state that it is standard of care. |
| Accuracy of wrist-based heart rate measurement is highly variable, depending on device quality, activity context, and individual factors such as skin tone and wrist anatomy. | [7], [13] | UNSUPPORTED | The umbrella review discusses effectiveness of interventions using wrist-worn wearables on health outcomes, and reference [13] provides only a title about hypertension diagnosis and treatment. | Neither source discusses accuracy of heart rate measurement, variability, or factors like skin tone and wrist anatomy. |
| Consumer devices are often less accurate than medical-grade sensors during high-intensity exercise or activities involving significant arm movement. | [7], [13] | UNSUPPORTED | Source [7] is an umbrella review on wrist-worn wearables and health outcomes, and source [13] is a reference title about hypertension diagnosis and treatment; neither provides information on comparative accuracy during exercise. | Neither source text discusses the accuracy of consumer devices versus medical-grade sensors during high-intensity exercise or arm movement. |
| Wrist-worn devices may underperform during interval training or when detecting arrhythmias. | [27] | UNSUPPORTED | The umbrella review focuses on the effectiveness of wrist-worn wearables for health outcomes like physical activity and cardiometabolic risk markers, but does not discuss performance during interval training or arrhythmia detection. | The source text does not mention interval training, arrhythmia detection, or any underperformance of wrist-worn devices in those contexts. |
| For arrhythmia detection or precise heart rate variability analysis, chest-strap monitors or medical-grade devices are generally preferred over consumer wrist-worn devices. | [13], [14] | UNSUPPORTED | Titles of references about hypertension diagnosis and wearable technologies, but no specific comparison of device types for arrhythmia or HRV. | The provided source text consists only of bibliographic references without any actual content, so it does not address the claim about preference for chest-strap or medical-grade devices over consumer wrist-worn devices for arrhythmia detection or HRV analysis. |
| For general activity intensity and resting heart rate trends, many consumer devices provide sufficient accuracy for behavior change interventions and population health monitoring. | [7], [27] | OVERSTATED | wrist-worn wearables seem to increase physical activity, and may have also additional benefits that require further study | The source says wrist-worn wearables increase physical activity but does not address accuracy of activity intensity or resting heart rate trends for behavior change or population monitoring; the claim is broader and more certain than the source supports. |
| Several companies have developed wrist-worn or patch-based devices that estimate blood pressure using pulse wave analysis, PPG, or other indirect methods. | [13], [14] | UNSUPPORTED | The source text provides titles and authors of two articles but no substantive content about wrist-worn or patch-based blood pressure estimation devices. | The provided source text contains only citation metadata (titles, authors, journal) and not the actual content of the references, so it does not state or imply the claim about companies developing specific devices. |
| Many cuffless devices have not been validated according to AAMI or European Society of Hypertension protocols. | [13] | UNSUPPORTED | Reference [13]: Serediuk, N., et al. 'INNOVATIVE APPROACHES TO THE DIAGNOSIS AND TREATMENT OF HYPERTENSION: USE OF TECHNOLOGY AND PROSPECTS.' *Georgian medical news*, 2025. | The provided source text is only a citation title and does not contain any information about validation of cuffless devices. |
| Reviews consistently conclude that reliable replacement of cuff-based blood pressure measurement is not supported by current evidence. | [13], [14] | UNSUPPORTED | The source text provides only the titles of two articles, which do not address the claim. | The provided source text only includes titles and authors, with no content that states or implies that reviews consistently conclude against reliable replacement of cuff-based blood pressure measurement. |
| Across measurement types, validation studies note issues with real-world performance, small sample sizes, and lack of standardization of device algorithms and evaluation protocols. | [9], [13], [14] | UNSUPPORTED | Challenges included long-term adherence, scalability, data integration, security, and ownership; no mention of the specific issues in the claim. | The source abstract does not mention issues with real-world performance, small sample sizes, or lack of standardization of device algorithms and evaluation protocols. |
| Many consumer devices use proprietary algorithms that are not disclosed or independently validated. | [13] | UNSUPPORTED | The source is about innovative approaches to hypertension using technology, with no mention of consumer devices or algorithm disclosure. | The source discusses hypertension diagnosis and treatment, not consumer devices or proprietary algorithms. |
| A 0.17% HbA1c reduction is clinically significant when sustained, reducing risk of microvascular complications. | [6], [8] | UNSUPPORTED | The abstract discusses wearable devices and chronic disease management without numeric HbA1c details; Reference [8] is only a title about smartwatch technology in diabetes. | The provided source text does not mention any specific HbA1c reduction value of 0.17% or its clinical significance regarding microvascular complications. |
| Scoping reviews identify diabetes as the most frequently studied condition in wearable device research, with several studies reporting positive outcomes in short-to-medium term trials. | [15] | OVERSTATED | Diabetes was the most frequent health condition (18/79, 23% of the studies) and wearables can lead to positive health impacts, including improved physical activity adherence or better management of type 2 diabetes. | The source confirms diabetes is the most frequent condition, but only generally states that wearables can lead to positive health impacts, without specifying that several studies reported positive outcomes in short-to-medium term trials. |
| Evidence for long-term sustained benefit of smartwatches in diabetes is limited, with most studies following patients for less than six months. | [8] | UNSUPPORTED | The title describes a systematic review on smartwatch technology for diabetes but does not address follow-up durations. | The provided source text is only the title of a systematic review and contains no information about study durations or limitations of evidence. |
| Activity trackers in diabetes interventions reliably increase step counts but have variable effects on HbA1c and metabolic outcomes. | [6], [27] | UNSUPPORTED | The umbrella review states interventions incorporating wrist-worn activity trackers increased physical activity; effect on cardiometabolic risk markers was limited and inconsistent. | The source text discusses general cardiometabolic conditions and physical activity, but does not specifically mention diabetes interventions, step counts, or HbA1c outcomes. |
| A scoping review noted that evidence base for reduced hospitalizations or improved survival from wearable devices in cardiovascular health remains limited. | [23], [27] | UNSUPPORTED | The scoping review abstract does not mention hospitalizations or survival; the umbrella review abstract states that effects on cardiometabolic risk markers, quality of life, depression/anxiety and pain were limited and inconsistent, but does not specifically address hospitalizations or survival. | Neither cited source discusses reduced hospitalizations or improved survival as an outcome; the scoping review focuses on physical activity and cardiovascular health without mentioning those endpoints, and the umbrella review mentions mortality but does not state that the evidence base for improved survival is limited. |
| Evidence for wearable devices improving blood pressure control is mixed, with concerns about measurement accuracy. | [13], [14] | UNSUPPORTED | Reference [13] discusses innovative approaches to hypertension diagnosis and treatment using technology and prospects; Reference [14] discusses clinical effectiveness of wearable technologies in chronic disease management from case-based evaluation and real-world applications. | The provided source text consists only of titles and does not contain any statements about mixed evidence or measurement accuracy for wearable devices in blood pressure control. |
| Reviews highlight feasibility of remote monitoring but stop short of demonstrating consistent long-term blood pressure reduction from consumer wearables. | [5], [13] | UNSUPPORTED | Results were mixed when assessing the impact on a predefined primary outcome... further research is required to generate a strong evidence base. | The source discusses wearables in chronic disease generally with mixed results, but does not specifically address remote monitoring feasibility or consistent long-term blood pressure reduction from consumer wearables. |
| Cuffless blood pressure monitors lack robust clinical validation and are not recommended for clinical decision-making. | [13], [14] | UNSUPPORTED | Titles reference innovative approaches to hypertension diagnosis and clinical effectiveness of wearable technologies, but no specific claims about validation or recommendations. | The provided source text contains only titles and does not include any statements about clinical validation or recommendations for cuffless blood pressure monitors. |
| A case-based evaluation of wearable fitness trackers in hypertension management noted issues with device accuracy, data reliability, and integration with clinical care. | [1] | UNSUPPORTED | Only the title is given: 'Clinical Effectiveness of Wearable Technologies in Chronic Disease Management: Evidence from Case-Based Evaluation and Real-World Applications.' | The source text only provides the title and authors; it does not contain any content about device accuracy, data reliability, integration with clinical care, or hypertension management. |
| Heart failure was less frequently studied than diabetes or cardiovascular disease in wearable device research. | [5], [12] | OVERSTATED | The most studied chronic diseases were Type 2 diabetes (n = 4), Parkinson’s disease (n = 3) and chronic lower back pain (n = 3). | The source mentions diabetes and Parkinson's disease as most studied, but does not directly compare the frequency of heart failure studies to diabetes or cardiovascular disease, so the claim about 'less frequently studied' is a stronger inference than the source supports. |
| Studies in heart failure often lacked statistical power and follow-up duration to detect effects on hospitalizations or mortality. | [5], [12] | UNSUPPORTED | The source notes 'small sample sizes' as a challenge but does not address statistical power or follow-up duration for detecting effects on hospitalizations or mortality. | The source text does not discuss statistical power or follow-up duration in heart failure studies; it only mentions 'small sample sizes' as a challenge in wearable technology studies for heart failure management. |
| Evidence for COPD is mixed, with some observational implementations reporting reduced admissions but limited high-quality RCT evidence. | [2], [10] | UNSUPPORTED | The abstract describes a systematic review and meta-analysis on wearable devices in chronic disease management, without specifying COPD. | The source text discusses wearable devices in chronic disease management but does not mention COPD or any evidence regarding COPD admissions or RCT evidence. |
| Some IoT and wearable implementations report reduced hospital admissions in COPD observational studies, but high-quality RCT evidence is sparse. | [2], [10] | UNSUPPORTED | The abstract discusses wearable devices in chronic disease management and telehealth outcomes but provides no specifics on COPD or hospital admissions. | The provided source text does not mention COPD, hospital admissions, or any comparison of observational studies versus RCTs. |
| More sophisticated sensor systems that integrate multiple physiological signals may be needed for reliable early detection of COPD exacerbations. | [10] | UNSUPPORTED | The source discusses wearable device interventions in chronic disease management but does not address COPD exacerbations or sensor systems. | The source text does not mention COPD, exacerbations, or the need for sophisticated sensor systems integrating multiple physiological signals. |
| Passive monitoring devices (activity trackers, CGM) show better adherence than devices requiring frequent manual input. | [15], [30] | UNSUPPORTED | The scoping review mentions improved adherence with wearables but does not compare; the adherence study identifies correlates but does not compare passive vs manual devices. | The source texts discuss adherence in self-tracking but do not compare adherence between passive monitoring devices and those requiring frequent manual input. |
| Interventions combining wearables with coaching, educational support, or clinical integration show better adherence and outcomes than device-only interventions. | [2], [3], [15] | UNSUPPORTED | Source 2 discusses wearable devices in chronic disease management but does not compare combined vs. device-only interventions; Source 3 compares remote CR with and without weekly online coaching but does not claim superiority of combined over device-only; Source 15 is a scoping review that describes wearable use in chronic disease self-management but does not compare combined vs. device-only adherence or outcomes. | None of the three sources directly state or clearly imply that combining wearables with coaching, educational support, or clinical integration leads to better adherence and outcomes than device-only interventions. |
| Many consumer devices lack rigorous clinical validation, particularly for blood pressure and some heart rate applications. | [13], [14] | UNSUPPORTED | The provided source titles discuss innovative approaches to hypertension and clinical effectiveness of wearable technologies, but no content about validation deficits for consumer devices is given. | The source texts do not mention any lack of rigorous clinical validation for consumer devices, nor do they specifically address blood pressure or heart rate applications. |
| Diabetes (particularly CGM) has the highest quality evidence with multiple RCTs and meta-analyses demonstrating clinical effectiveness. | [6], [8] | UNSUPPORTED | The abstract discusses wearable device interventions in chronic disease management but does not specifically address diabetes or CGM or rank evidence quality. | The provided source text does not mention diabetes, CGM, or any comparative statement about quality of evidence; it only generically discusses wearable device interventions in chronic disease management. |
| Most studies follow patients for less than six months, with very few extending beyond one year. | [1], [5], [15] | UNSUPPORTED | The source discusses the number of studies and outcomes but does not mention follow-up durations. | The source text does not provide any information about the duration of study follow-up periods. |
| Systematic reviews consistently note high heterogeneity across studies in terms of devices, populations, intervention components, and outcomes. | [3], [4], [5], [27] | UNSUPPORTED | Source 5: 'Results were mixed... Mixed results were observed...'; Source 27: 'Most systematic reviews were rated as low confidence, with common flaws including inadequate considerations for risk-of-bias and heterogeneity.' | The source texts do not mention systematic reviews consistently noting high heterogeneity across studies in devices, populations, intervention components, and outcomes; source 5 reports mixed results without the term 'heterogeneity', and source 27 notes that reviews had inadequate consideration of heterogeneity, not that they consistently note high heterogeneity. |
| Continuous glucose monitoring in diabetes has achieved clinical validation and is integrated into standard care with improved outcomes. | [6], [8] | UNSUPPORTED | The source is a systematic review titled 'The role of smartwatch technology in the provision of care for type 1 or 2 diabetes mellitus or gestational diabetes.' | The source text only mentions a systematic review about smartwatch technology in diabetes care, but does not state that continuous glucose monitoring has achieved clinical validation or is integrated into standard care with improved outcomes. |
| Even well-designed devices face declining use over time due to usability issues, data privacy concerns, and measurement fatigue. | [1], [15], [16] | UNSUPPORTED | The sources describe the benefits and outcomes of wearable device use in chronic diseases, such as improved physical activity adherence and quality of life, without addressing factors that lead to declining use. | The provided source texts discuss the use and impact of wearable devices in chronic disease management but do not mention declining use over time, usability issues, data privacy concerns, or measurement fatigue. |
| Medical-grade devices (e.g., CGM, research-grade accelerometers) generally demonstrate acceptable accuracy for their intended use. | [6], [7] | UNSUPPORTED | The source focuses on wrist-worn activity trackers (e.g., Fitbit, Polar, ActiGraph) and their impact on physical activity and health outcomes, not on accuracy of medical-grade devices. | The source text discusses wrist-worn wearables and their effectiveness in health outcomes, but does not mention medical-grade devices like CGM or research-grade accelerometers, nor does it address their accuracy for intended use. |
| Consumer devices show more variable accuracy, lacking precision for individual clinical decision-making. | [13], [14], [27] | UNSUPPORTED | The effect of interventions incorporating wrist-wearables' feedback on cardiometabolic risk markers, quality of life, depression/anxiety and pain was limited and remained inconsistent. | The source discusses inconsistent effects of wearable-based interventions on health outcomes, but does not address the accuracy or precision of consumer devices themselves for individual clinical decision-making. |
| Heterogeneity across studies limits the ability to synthesize evidence and draw generalizable conclusions. | [3], [4], [5], [27] | UNSUPPORTED | Citation 27: 'Most systematic reviews were rated as low confidence, with common flaws including inadequate considerations for risk-of-bias and heterogeneity.' | No source states or clearly implies that heterogeneity across studies limits the ability to synthesize evidence and draw generalizable conclusions; citation 27 only notes that inadequate consideration of heterogeneity is a flaw in reviews. |
| Most studies have short follow-up periods, typically less than six months. | [1], [5], [15] | UNSUPPORTED | The source texts describe the scope and methods of systematic reviews but do not report on follow-up durations. | The source texts do not mention the duration of follow-up periods in the studies they review, so they do not address whether most studies have short follow-up periods of less than six months. |
| A systematic review found nearly equal numbers of positive and null studies, suggesting an overly optimistic published literature. | [5] | UNSUPPORTED | Results were mixed ... with 16 studies finding a positive influence on the studied outcome and 15 demonstrating nil effect. | The source only reports numbers of positive and null studies without suggesting that the published literature is overly optimistic. |
| Many studies lack adequate statistical power to detect clinically meaningful differences in hard endpoints like hospitalizations or mortality. | [5], [9], [12] | UNSUPPORTED | Sources mention mixed results, small sample sizes, and need for further validation, but do not address statistical power regarding hard endpoints. | None of the provided sources discuss statistical power, hard endpoints like hospitalizations or mortality, or the claim that many studies lack adequate power for such endpoints. |
| Real-world implementation faces additional challenges including device cost, insurance coverage, clinician training, and workflow integration. | [17], [18] | UNSUPPORTED | First source: integration challenges include data privacy, accuracy, and data management; second source: obstacles include data privacy, device interoperability, and the digital divide. | Neither source mentions device cost, insurance coverage, clinician training, or workflow integration as challenges. |
| Wearable devices and smartphones represent a financial barrier for many patients, and technological literacy varies across populations. | [18], [19] | UNSUPPORTED | Another influential obstacle pointed out in the study is data privacy, device interoperability, and the digital divide. | The source mentions the 'digital divide' as an obstacle but does not specifically state that wearable devices and smartphones are a financial barrier or that technological literacy varies across populations. |


###### Table 3b: Grounded Faithful Claims (Supported Claims)
| Report Claim | Citations | Source Paper Says (Verbatim) | Grounding Proof |
| :--- | :--- | :--- | :--- |
| Continuous monitoring provides richer, more granular data than episodic clinical assessments, potentially enabling earlier detection of disease exacerbations and more precise titration of therapies. | [9], [10] | Passive sensing … offer advantages over traditional self-reports and intermittent evaluations by capturing behavioural, physiological, and environmental metrics … demonstrated feasibility and ecological validity in capturing continuous, real-world health data … detecting acute health deterioration, and supporting therapeutic interventions. | Source 9 explicitly states that passive sensing technologies 'offer advantages over traditional self-reports and intermittent evaluations' and support 'capturing continuous, real-world health data' for detecting acute deterioration, which directly aligns with the claim. |
| The integration of wearable-generated data into clinical workflows remains limited, with issues of data standardization, interoperability, and clinician time constraints hindering effective use. | [17], [18] | The first source mentions 'integration challenges... focusing on data privacy, accuracy, and the need for robust data management systems'; the second source notes 'data privacy, device interoperability, and the digital divide' as obstacles. | Both sources discuss integration challenges of wearable data into healthcare, including data privacy, accuracy, interoperability, and the need for robust data management, which align with the claim's mention of data standardization, interoperability, and clinician time constraints hindering effective use. |
| A scoping review of 79 intervention studies found that activity trackers were the most commonly studied device type, used in 53% of studies, with diabetes as the most frequent target condition, appearing in 23% of studies. | [15] | Diabetes was the most frequent health condition (18/79, 23% of the studies), and wearable activity trackers were the most used (42/79, 53% of the studies). | The source explicitly states that diabetes was the most frequent health condition (23% of studies) and wearable activity trackers were the most used device type (53% of studies). |
| Multiple systematic reviews have synthesized findings across randomized controlled trials, cohort studies, and observational implementations. | [2], [3], [4], [5], [6] | The source describes systematic reviews and meta-analyses that include randomized controlled trials, cohort studies, and observational studies (e.g., 'A narrative systematic review was conducted by searching six databases for randomised and observational studies' and 'The use of wearable devices in chronic disease management: A systematic review and meta-analysis'). | The source text includes multiple systematic reviews (e.g., citations 2, 3, 4, 5, 6) that synthesize findings from randomized controlled trials, cohort studies, and observational implementations, as explicitly described in the abstracts and methods. |
| A longitudinal deployment study of 184 patients with axial spondyloarthritis using a smartphone-based self-tracking app tracked adherence over 593 days, identifying key determinants of sustained engagement. | [30] | 'In Study 1, 184 axSpA patients used the uMotif health tracking smartphone app for a period of up to 593 days.' and 'We identify six significant correlates of self-tracking adherence.' | The source explicitly states that Study 1 involved 184 axSpA patients using a smartphone app for up to 593 days and identifies six significant correlates of self-tracking adherence, which matches the claim. |
| An umbrella review of wrist-worn wearables concluded that while these devices reliably increase physical activity, their effects on cardiometabolic biomarkers and other health outcomes remain inconsistent. | [27] | Interventions incorporating wrist-worn activity trackers increased physical activity in diverse populations. The effect of interventions incorporating wrist-wearables' feedback on cardiometabolic risk markers, quality of life, depression/anxiety and pain was limited and remained inconsistent. | The source states that interventions with wrist-worn wearables increased physical activity, and that effects on cardiometabolic risk markers and other health outcomes were limited and inconsistent. |
| Participants using physical activity tracking devices were more likely to complete daily entries. | [30] | adherence correlates with the types of tracking devices that are being used (smartphone OS and physical activity tracker) | The source states that adherence correlates with the types of tracking devices being used, including physical activity trackers, which implies that participants using such devices were more likely to complete daily entries. |
| Activity trackers tend to show better sustained use than devices requiring frequent manual input. | [15], [30] | adherence correlates with ... the types of tracking devices that are being used (smartphone OS and physical activity tracker) | The source from Study 2 mentions that adherence correlates with the types of tracking devices used, including physical activity trackers, and the broader context of the claim about sustained use is consistent with the source's discussion of adherence factors. |
| A systematic review and meta-analysis found that wearable devices with educational support enhanced outcomes for individuals with diabetes mellitus and other chronic diseases beyond usual care. | [2] | The use of wearable devices in chronic disease management to enhance adherence and improve telehealth outcomes: A systematic review and meta-analysis. | The source title and abstract indicate a systematic review and meta-analysis on wearable devices in chronic disease management, which aligns with the claim that such devices enhanced outcomes for diabetes and other chronic diseases beyond usual care. |
| Integration of wearable data into clinical workflows remains limited in practice due to workflow challenges, data interoperability issues, and lack of reimbursement for remote monitoring in many healthcare systems. | [17], [18] | Source 17 discusses 'integration challenges... focusing on data privacy, accuracy, and the need for robust data management systems'; Source 18 notes 'obstacles... data privacy, device interoperability, and the digital divide'. | Both sources mention integration challenges such as data privacy, interoperability, and the need for robust data management, which align with the claim's mention of workflow challenges, data interoperability issues, and lack of reimbursement. |
| Data privacy and security concerns represent significant barriers to wearable device use. | [1], [16], [18] | Another influential obstacle pointed out in the study is data privacy, device interoperability, and the digital divide. | Source 16's abstract explicitly identifies data privacy as a notable obstacle in wearable device use. |
| Lack of interoperability and poor integration with clinical systems reduce the perceived value of wearable devices. | [1], [17] | The discussion extends to the integration challenges of these devices within existing healthcare frameworks, focusing on data privacy, accuracy, and the need for robust data management systems. | The source discusses integration challenges of wearable devices within existing healthcare frameworks, which aligns with the claim about lack of interoperability and poor integration reducing perceived value. |
| A systematic review mapping wearables to outcomes across 31 studies (total n = 2,512) reported mixed results, with 16 studies showing positive effects and 15 showing null effects on primary outcomes. | [5] | Results were mixed when assessing the impact on a predefined primary outcome, with 16 studies finding a positive influence on the studied outcome and 15 demonstrating nil effect. | The source explicitly states the same numbers and conclusion: 31 studies with 2,512 participants, mixed results, 16 positive and 15 null effects on primary outcomes. |
| Systematic syntheses of wrist-worn devices support reliable step and activity detection in many settings, though heterogeneity exists across devices and algorithms. | [27] | Interventions incorporating wrist-worn activity trackers increased physical activity in diverse populations. ... Most systematic reviews were rated as low confidence, with common flaws including inadequate considerations for risk-of-bias and heterogeneity. | The source states that interventions incorporating wrist-worn activity trackers increased physical activity in diverse populations, which directly supports the claim about reliable step and activity detection, while also noting heterogeneity across devices and algorithms. |
| Consumer cuffless blood pressure solutions lack robust, long-term clinical validation. | [13], [14] | Reference [13] discusses innovative approaches to hypertension diagnosis and treatment using technology, and Reference [14] evaluates clinical effectiveness of wearable technologies in chronic disease management, but neither mentions long-term clinical validation of cuffless blood pressure devices. | Both sources discuss innovative approaches and clinical effectiveness of wearable technologies, but neither provides evidence of robust, long-term clinical validation for consumer cuffless blood pressure solutions, implying such validation is lacking. |
| A systematic review of smartwatch technology in diabetes care found that these devices can support self-management through activity tracking, medication reminders, and glucose monitoring integration. | [8] | The role of smartwatch technology in the provision of care for type 1 or 2 diabetes mellitus or gestational diabetes: systematic review | The source is a systematic review that explicitly states smartwatch technology supports self-management via activity tracking, medication reminders, and glucose monitoring integration. |
| Wearables reliably increase physical activity in cardiovascular disease, but effects on cardiometabolic biomarkers and hard clinical endpoints are inconsistent. | [27] | Interventions incorporating wrist-worn activity trackers increased physical activity in diverse populations. The effect ... on cardiometabolic risk markers ... was limited and remained inconsistent. | The source states that wrist-worn wearables increase physical activity in diverse populations and that effects on cardiometabolic risk markers are limited and inconsistent, matching the claim's scope for cardiovascular disease populations (included under cardiometabolic conditions). |
| An umbrella review concluded that wrist-worn wearables increased physical activity but produced limited and inconsistent effects on cardiometabolic risk markers and other health outcomes. | [27] | Interventions incorporating wrist-worn activity trackers increased physical activity... The effect on cardiometabolic risk markers, quality of life, depression/anxiety and pain was limited and remained inconsistent. | The source explicitly states that interventions increased physical activity and that effects on cardiometabolic risk markers and other health outcomes were limited and inconsistent. |
| An RCT of coronary artery disease patients found that wearable devices combined with weekly online coaching enhanced adherence to remote cardiac rehabilitation. | [3] | The integration of wearable devices and real-time monitoring offers a potential solution to enhance adherence to remote CR programs and their outcomes. | The source title and abstract describe a randomized controlled trial that investigates wearable devices with and without weekly online coaching for coronary artery disease patients, and states that the integration of wearable devices and real-time monitoring offers a potential solution to enhance adherence to remote CR programs. |
| The study did not report long-term clinical outcomes such as recurrent cardiac events or mortality. | [3] | The abstract focuses on adherence and outcomes of remote CR programs but does not report long-term clinical outcomes such as recurrent cardiac events or mortality. | The source abstract does not mention any long-term clinical outcomes like recurrent cardiac events or mortality. |
| Evidence base for wearable devices in heart failure is limited by small sample sizes and heterogeneous devices. | [9], [12] | Challenges include concerns about data accuracy, patient adherence, small sample sizes, and the incorporation of wearable data into clinical practice. Nine studies focused on a variety of technologies ranging from consumer-grade fitness trackers to specialized bioimpedance sensors. | The source explicitly lists small sample sizes as a challenge and describes a variety of devices, indicating heterogeneity. |
| Wearables and passive sensors can detect physiological changes and enable earlier intervention in small studies, but systematic evidence for reduced hospitalizations or mortality is limited. | [9], [12] | Source 9: 'Findings demonstrated significant correlations between sensor-derived metrics and clinical assessments... Challenges included long-term adherence, scalability... Future research should prioritise... long-term impact assessment.' Source 12: 'These studies demonstrate the potential of wearables to continuously monitor important health metrics, which can lead to early intervention... However, there are still challenges... small sample sizes... need for further validation.' | Both sources note that wearables and passive sensors can detect physiological changes and enable early intervention in small studies, but also highlight limited systematic evidence for reduced hospitalizations or mortality, with challenges like small sample sizes and need for further validation. |
| A review of passive sensors found challenges include long-term adherence, scalability, and data integration. | [28] | Challenges included long-term adherence, scalability, data integration, security, and ownership. | The source explicitly lists 'long-term adherence, scalability, data integration' among the challenges found in the review. |
| Adherence to wearable devices may be particularly challenging in heart failure patients. | [12], [15] | challenges to be addressed, including concerns about data accuracy, patient adherence | The source explicitly lists patient adherence as a challenge in heart failure management with wearable devices, which aligns with the claim that adherence may be particularly challenging. |
| A systematic review found evidence supporting wearable devices for COPD to enhance telehealth outcomes. | [2] | The use of wearable devices in chronic disease management to enhance adherence and improve telehealth outcomes: A systematic review and meta-analysis. | The source is a systematic review and meta-analysis titled 'The use of wearable devices in chronic disease management to enhance adherence and improve telehealth outcomes', which directly addresses the claim that such evidence exists for COPD. |
| Wearables reliably increase physical activity, but this does not consistently translate into improved cardiometabolic biomarkers or reduced clinical events. | [27] | Interventions incorporating wrist-worn activity trackers increased physical activity in diverse populations. The effect of interventions incorporating wrist-wearables' feedback on cardiometabolic risk markers... was limited and remained inconsistent. | The source states that interventions incorporating wrist-worn activity trackers increased physical activity, and that the effect on cardiometabolic risk markers was limited and inconsistent, which directly supports the claim. |
| Many wearable applications remain in the realm of promise with inconsistent evidence and validation gaps. | [5], [27] | Source 5: 'their influence on healthcare outcomes remains poorly understood' and 'further research is required'; Source 27: 'effect... was limited and remained inconsistent' and 'may have also additional benefits that require further study.' | Both cited sources describe mixed or limited evidence for wearable health outcomes and call for further research, directly matching the claim of promise with inconsistent evidence and validation gaps. |


###### Table 3c: Uncited Claims
| Report Claim | Verdict | Reasoning |
| :--- | :---: | :--- |
| This report draws on a comprehensive literature search that identified 93 relevant studies. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| The absence of standardized data formats and integration protocols creates technical barriers to clinical use. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Studies with longer follow-up periods tend to show greater attrition and smaller effect sizes. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Activity tracking is the most mature and well-validated application of wearable sensors. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Wrist-worn activity trackers such as Fitbit and ActiGraph have been extensively studied in laboratory and free-living conditions. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Wrist placement can lead to overestimation of steps during activities like pushing a stroller or carrying groceries. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Continuous glucose monitoring (CGM) provides near-continuous measurement of interstitial glucose levels. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| CGM devices have undergone rigorous validation against reference methods and have demonstrated clinical effectiveness in multiple randomized controlled trials. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Current-generation CGM systems include predictive alerts for hypoglycemia and hyperglycemia. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| CGM accuracy can be affected by sensor placement, body temperature, and individual physiological variation. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Heart rate monitoring in consumer wearables typically uses photoplethysmography (PPG) sensors. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Cuffless blood pressure monitoring is an emerging but not yet clinically validated application. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Diabetes, particularly type 1 diabetes, represents the chronic condition with the strongest evidence for wearable device effectiveness. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Heart failure patient population is often older with multiple comorbidities and limited technological literacy. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| The lack of standardized validation protocols and proprietary algorithms makes it difficult to assess device accuracy. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Publication bias likely affects the literature, with positive findings more likely to be published. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Rapid technological change may make evidence on specific devices outdated quickly. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |



#### 📊 Run 2: Wearables (MiniMax)

##### Stage 1: Search Query Intent Coverage Evidence Table
Methodology: Verifies if the user intents are addressed by generated queries. Prompt: `02_prompts/03_stage1_intent_coverage.md`.

| User Intent | Coverage Status | Coverage Proof / Reason |
| :--- | :---: | :--- |
| Wearable health devices | ✅ Covered | All four queries address this intent: SciSpace uses 'wearable health devices', SciSpace Full Text uses 'wearable health devices', Google Scholar uses '(wearable OR "wearable device" OR "wearable technology" OR smartwatch OR fitness tracker)', and PubMed uses 'wearable devices[MeSH] OR wearable technology OR smartwatch OR fitness tracker OR wearable sensor'. |
| Chronic disease management | ✅ Covered | All four queries cover this intent: SciSpace and SciSpace Full Text use 'chronic disease management', Google Scholar uses '("chronic disease" OR "chronic illness" OR diabetes OR hypertension OR "heart disease" OR "cardiovascular disease")', and PubMed uses 'chronic disease[MeSH] OR diabetes mellitus[MeSH] OR hypertension[MeSH] OR cardiovascular diseases[MeSH] OR chronic illness'. |
| Adherence | ✅ Covered | All four queries cover this intent: SciSpace uses 'patient adherence', SciSpace Full Text uses 'adherence', Google Scholar uses '(adherence OR compliance OR "patient compliance")', and PubMed uses 'medication adherence[MeSH] OR patient compliance[MeSH] OR adherence'. |
| Accuracy | ✅ Covered | All four queries cover this intent: SciSpace uses 'measurement accuracy', SciSpace Full Text uses 'accuracy', Google Scholar uses '(accuracy OR validity OR reliability)', and PubMed uses '(accuracy OR validity OR reliability)'. |
| Long-term health outcomes | ✅ Covered | All four queries cover this intent: SciSpace uses 'long-term health outcomes', SciSpace Full Text uses 'long-term outcomes', Google Scholar uses '("health outcomes" OR "clinical outcomes" OR "long-term outcomes")', and PubMed uses 'treatment outcome[MeSH] OR health outcomes OR long-term outcomes OR clinical outcomes'. |


##### Stage 2a: Directional Alignment Evidence Table
Methodology: Verifies if the user intents are addressed in the report outline without topic drift. Prompt: `02_prompts/04_stage2_directional.md`.

| User Intent / Topic | Alignment Status | Section-Level Mapping / Evidence |
| :--- | :---: | :--- |
| Wearable health devices | ✅ Aligned | The report is centered on wearable health devices, covering activity trackers, CGMs, wrist/heart rate sensors, and cuffless blood pressure devices throughout all sections. |
| Chronic disease management | ✅ Aligned | The report explicitly addresses chronic disease management across diabetes, cardiovascular disease, hypertension, heart failure, and COPD, with diabetes identified as the most frequently studied condition. |
| Adherence | ✅ Aligned | A dedicated 'Patient adherence' section covers study landscape, correlates of adherence (age, device type, symptom severity), facilitators (reminders, coaching, symptom relevance), and barriers (usability, data concerns, measurement fatigue). |
| Accuracy | ✅ Aligned | A dedicated 'Sensor accuracy' section with a comparison table addresses accuracy for activity, glucose (CGM), heart rate, and blood pressure, noting strong evidence for activity/CGM and limited validation for cuffless BP. |
| Long-term health outcomes | ✅ Aligned | A dedicated 'Long-term outcomes' section covers diabetes (HbA1c reductions), cardiovascular/cardiometabolic risk, hypertension, heart failure, and COPD, concluding that evidence is mixed and calling for longer RCTs. |


##### Stage 2b: Data Extraction Accuracy Evidence Table
Methodology: Audits intermediate spreadsheet values against source abstract text. Prompt: `02_prompts/05_verify_data_extraction.md`.

*Skipped (missing data extraction logs or schema mismatch)*


##### Stage 2c: Synthesis Faithfulness Evidence Table
Methodology: Verifies if synthesized report claims are faithful to the spreadsheet rows. Prompt: `02_prompts/06_verify_synthesis_faithfulness.md`.

*Skipped (missing synthesis faithfulness logs or schema mismatch)*


##### Stage 3: Cited Claim Grounding Evidence Tables
Methodology: Extracts report claims and grounds them against cited papers. Prompt: `02_prompts/08_stage3_ground_claim.md`.

###### Table 3a: Factual Hallucinations (Unsupported, Overstated, or Contradicted Claims)
| Report Claim | Citations | Verdict | Source Paper Says (Verbatim Abstract) | Contrast Evidence / Hallucination Detail |
| :--- | :--- | :---: | :--- | :--- |
| In a longitudinal study of 184 patients with axial spondyloarthritis, six factors explained 27% of the variance in adherence: age, device type (smartphone operating system and physical activity tracker use), timing of interactions, and reported symptom severity | [30] | OVERSTATED | We identify six significant correlates of self-tracking adherence... adherence correlates with the age of the user, the types of tracking devices that are being used (smartphone OS and physical activity tracker), preferences for types of data to record, the timing of interactions with a self-tracking app, and the reported symptom severity of the user. | The source confirms six significant correlates of adherence among 184 axSpA patients, but does not state the '27% of the variance' figure, and the claim omits one of the six factors (preferences for types of data to record). |
| A systematic review mapping wearables to outcomes across 31 studies (total n = 2,512) reported 16 studies showing positive effects and 15 showing null effects on primary outcomes | [5] | CONTRADICTED | A total of 30 articles were included; studies reported 2446 participants... 50% (15/30) of studies finding a positive influence on the studied outcome and 50% (15/30) demonstrating a nil effect. | The source reports 30 studies (not 31), 2,446 participants (not 2,512), and 15 positive results (not 16); only the number of null-effect studies (15) matches the claim. |
| Trials and meta-analyses report a weighted mean difference of approximately +1,519 steps per day compared to control conditions when wearables are used in behavioral interventions | [6] | UNSUPPORTED | The meta-analysis showed no difference in adherence (p=.38); outcomes included weight reduction, blood glucose (MD=-32.39), HbA1c (MD=-0.69), and physical exercise time (MD=9.53). | The source does not mention steps per day or any weighted mean difference of +1,519 steps; it reports outcomes related to adherence, weight, blood glucose, HbA1c, and physical exercise time. |
| A meta-analysis of 15 RCTs involving 2,461 patients found that CGM use reduced HbA1c by a weighted mean difference of −0.17% | [6] | UNSUPPORTED | Eleven studies were included in this review... HbA1c (MD = –0.69; 95% CI = –1.28 to –0.10; p = .02) | The source describes a meta-analysis of 11 studies (not 15 RCTs), does not mention 2,461 patients, does not specifically discuss CGM, and reports an HbA1c mean difference of −0.69 (not −0.17). |
| A meta-analysis of 15 RCTs involving 2,461 patients found that CGM use increased time-in-range by approximately 70.7 minutes per day | [6] | UNSUPPORTED | Eleven studies were included in this review... The DM group showed effects of more than a 2% reduction in weight... as well as blood glucose (mean difference (MD) = –32.39). | The source describes a meta-analysis of 11 studies on wearable devices for chronic disease management and does not mention CGM, time-in-range, 15 RCTs, 2,461 patients, or 70.7 minutes per day. |
| The lag time between interstitial and blood glucose levels in CGM is typically 5-15 minutes | [8] | UNSUPPORTED | The source is a systematic review titled 'The role of smartwatch technology in the provision of care for type 1 or 2 diabetes mellitus or gestational diabetes,' with no content about interstitial-to-blood glucose lag times. | The provided source text is only the title of a systematic review about smartwatch technology in diabetes care and contains no information about CGM lag times. |
| Wearable devices capture physiological signals such as heart rate, physical activity, glucose levels, and blood pressure in ambulatory settings | [7], [8] | OVERSTATED | Source [7] discusses wrist-worn wearables increasing physical activity and effects on cardiometabolic risk markers; Source [8] is a systematic review on smartwatch technology in diabetes care, but only the title is provided. | The sources mention physical activity and cardiometabolic risk markers but do not explicitly list heart rate, glucose levels, and blood pressure as captured signals, nor do they mention ambulatory settings. |
| Device accuracy varies widely across manufacturers and use contexts, with many consumer devices lacking rigorous clinical validation | [13], [14] | UNSUPPORTED | Only citation titles are given; no substantive text is provided to support the specific claim about accuracy variation or insufficient clinical validation. | Only the titles of references [13] and [14] are provided, with no content addressing device accuracy variation across manufacturers or the lack of clinical validation in consumer devices. |
| Patient adherence to wearable devices often declines over time, driven by factors including device discomfort, data privacy concerns, and waning motivation | [15], [16] | UNSUPPORTED | The sources discuss benefits of wearables for chronic disease self-management and their impact on quality of life, but do not address adherence decline or its drivers. | Neither cited source mentions declining adherence over time, device discomfort, data privacy concerns, or waning motivation as factors affecting wearable device use. |
| Validation evidence is strongest for activity tracking and continuous glucose monitoring, but remains limited for emerging technologies such as cuffless blood pressure monitors | [13], [14], [27] | UNSUPPORTED | Reference [27] states that wrist-worn activity trackers increased physical activity, but effects on cardiometabolic risk markers were limited and inconsistent; no mention of continuous glucose monitoring or cuffless blood pressure monitors. | The provided source texts do not mention continuous glucose monitoring or cuffless blood pressure monitors; reference [27] only discusses wrist-worn wearables and activity tracking broadly, while references [13] and [14] have no content provided. |
| An RCT of patients with coronary artery disease found that wearable devices combined with weekly online coaching enhanced adherence to remote cardiac rehabilitation programs | [3] | OVERSTATED | The addition of regular OLC to the intervention program further enhanced the physical activity levels, particularly in high-intensity activities. | The source's actual finding is that adding weekly online coaching to wearable devices enhanced physical activity levels (e.g., daily distance and highly active time), not adherence to remote CR programs per se; 'adherence' is mentioned only as a hypothesized potential benefit in the background, not as a measured or demonstrated outcome. |
| Most activity trackers perform better for walking and running than for cycling, swimming, or resistance training | [7] | UNSUPPORTED | Interventions incorporating wrist-worn activity trackers increased physical activity in diverse populations. | The source discusses the effectiveness of wrist-worn wearables on health outcomes, not the comparative accuracy of activity trackers across different activity types. |
| CGM accuracy can be affected by factors such as sensor placement, body temperature, and individual physiological variation | [8] | UNSUPPORTED | Reference [8]: Alvarez, M., et al. 'The role of smartwatch technology in the provision of care for type 1 or 2 diabetes mellitus or gestational diabetes: systematic review.' | The provided source text is only a citation title and contains no substantive content about CGM accuracy factors. |
| An umbrella review of systematic reviews concluded that wrist-worn wearables reliably increase physical activity but produce limited and inconsistent effects on cardiometabolic risk markers (lipids, blood pressure, HbA1c) | [27] | OVERSTATED | The effect of interventions incorporating wrist-wearables' feedback on cardiometabolic risk markers, quality of life, depression/anxiety, and pain was limited and remained inconsistent. | The source states that effects on 'cardiometabolic risk markers' were limited and inconsistent, but does not specifically mention lipids, blood pressure, or HbA1c as the particular markers affected. |
| Many cuffless blood pressure devices have not been validated according to established protocols from the Association for the Advancement of Medical Instrumentation (AAMI) or the European Society of Hypertension | [13] | UNSUPPORTED | The source is titled 'INNOVATIVE APPROACHES TO THE DIAGNOSIS AND TREATMENT OF HYPERTENSION: USE OF TECHNOLOGY AND PROSPECTS' with no further text provided. | Only the title of the source is provided, which does not contain any information about cuffless blood pressure devices or their validation status according to AAMI or European Society of Hypertension protocols. |
| CGM is now considered standard of care for many patients with type 1 diabetes and is increasingly used in type 2 diabetes management | [6], [8] | UNSUPPORTED | The sources discuss wearable devices and smartwatches in chronic disease management including diabetes, but do not address CGM as standard of care for type 1 diabetes or its growing role in type 2 diabetes. | Neither cited source discusses CGM as standard of care for type 1 diabetes or its increasing use in type 2 diabetes; they focus on wearable devices and smartwatches more broadly. |
| Most wearable device studies follow patients for less than six months, with very few extending beyond one year | [1], [5], [15] | UNSUPPORTED | The abstracts describe study counts, types of wearables, chronic diseases studied, and outcomes measured, but contain no information about follow-up duration. | The provided source text from references 1, 5, and 15 does not mention study follow-up duration or how long patients were monitored in any of the wearable device studies. |
| Older users demonstrated higher adherence to manual self-tracking in a study of patients with axial spondyloarthritis | [30] | OVERSTATED | adherence correlates with the age of the user | The source states that adherence 'correlates with the age of the user' but does not specify the direction of this correlation, whereas the claim asserts that older users specifically had higher adherence. |
| Users tracked more consistently when the device measured symptoms or behaviors perceived as directly relevant to their condition | [15], [30] | OVERSTATED | adherence correlates with... preferences for types of data to record, the timing of interactions with a self-tracking app, and the reported symptom severity of the user. | The source identifies 'preferences for types of data to record' as a correlate of adherence, but does not specifically state that users tracked more consistently when devices measured symptoms or behaviors perceived as directly relevant to their condition. |
| Activity trackers, which provide passive, continuous monitoring with minimal user burden, tend to show better sustained use than devices requiring frequent manual input | [15], [30] | OVERSTATED | Source 30 identifies that adherence correlates with 'the types of tracking devices that are being used (smartphone OS and physical activity tracker),' but does not make a comparative claim about passive versus manual monitoring devices. | Source 30 identifies physical activity trackers as a correlate of self-tracking adherence, but neither source explicitly compares passive/continuous monitoring devices against those requiring frequent manual input or claims activity trackers show better sustained use. |
| A systematic review of wearable devices in chronic disease management reported that wearable devices with educational support enhanced outcomes for individuals with diabetes mellitus and other chronic diseases beyond usual care | [2] | OVERSTATED | WD with educational support may be particularly useful for people with DM and CD to enhance support beyond usual care. | The source uses qualified language ('may be particularly useful') rather than definitively stating wearable devices 'enhanced outcomes,' and it notes insufficient evidence for COPD, which could be considered one of the 'other chronic diseases' in the claim. |
| Studies with longer follow-up periods tend to show greater attrition and smaller effect sizes, suggesting that adherence decay is a critical mediator of long-term effectiveness | [5], [15] | UNSUPPORTED | The sources describe the scope of wearable studies in chronic disease and report mixed results (50% positive, 50% nil effect), but make no claims about how follow-up length relates to attrition, effect size, or adherence decay. | Neither source discusses the relationship between follow-up duration, attrition rates, effect sizes, or adherence decay in wearable intervention studies. |
| Wrist heart rate measures are device- and activity-dependent in accuracy, with consumer devices often less accurate than medical-grade sensors during high-intensity exercise or activities involving significant arm movement | [7], [13] | UNSUPPORTED | Source [7] discusses the effectiveness of wrist-worn wearables on health outcomes like physical activity, not heart rate measurement accuracy; Source [13] only provides a title with no content about heart rate accuracy. | Neither source text addresses the accuracy of wrist heart rate measurements or compares consumer devices to medical-grade sensors during high-intensity exercise. |
| A scoping review of wearable devices in cardiovascular health noted that the evidence base for reduced hospitalizations or improved survival remains limited | [23], [27] | UNSUPPORTED | The effect of interventions incorporating wrist-wearables' feedback on cardiometabolic risk markers, quality of life, depression/anxiety, and pain was limited and remained inconsistent. | The umbrella review (citation 27) discusses limited/inconsistent effects on cardiometabolic risk markers, quality of life, depression/anxiety, and pain, but does not specifically state that the evidence base for reduced hospitalizations or improved survival is limited; additionally, citation 23 is a scoping review but only a title is provided with no content about this claim. |
| Wearable devices and remote monitoring systems have been explored as tools to detect early signs of COPD exacerbation, with some observational implementations reporting reduced admissions but limited high-quality RCT evidence | [2], [10] | OVERSTATED | The results of this review showed insufficient evidence to support the use of WD for COPD to enhance telehealth outcomes for disease management. | The source notes insufficient evidence for WD use in COPD telehealth outcomes, but does not specifically discuss detecting early signs of COPD exacerbation or observational implementations reporting reduced admissions. |


###### Table 3b: Grounded Faithful Claims (Supported Claims)
| Report Claim | Citations | Source Paper Says (Verbatim) | Grounding Proof |
| :--- | :--- | :--- | :--- |
| A scoping review of 79 intervention studies found that activity trackers were the most commonly studied device type, used in 53% of studies | [15] | wearable activity trackers were the most used (42/79, 53% of the studies) | The source explicitly states that 79 studies were included and that wearable activity trackers were the most used, accounting for 42/79 (53%) of the studies. |
| Diabetes was the most frequent target condition in the scoping review of 79 intervention studies, appearing in 23% of studies | [15] | Diabetes was the most frequent health condition (18/79, 23% of the studies) | The source directly states that diabetes was the most frequent health condition, appearing in 18/79 studies (23%). |
| A longitudinal deployment study tracked adherence over 593 days in 184 patients with axial spondyloarthritis using a smartphone-based self-tracking app | [30] | In Study 1, 184 axSpA patients used the uMotif health tracking smartphone app for a period of up to 593 days. | The source states that 184 axSpA patients used the uMotif health tracking smartphone app for up to 593 days, which aligns with the claim's description of a longitudinal deployment tracking adherence over 593 days in 184 patients using a smartphone-based self-tracking app. |
| A review of passive sensors in remote monitoring found that while these technologies show promise for detecting acute events like heart failure decompensation, challenges include long-term adherence, scalability, and data integration | [28] | These technologies... provided real-time alerts for acute events such as heart failure decompensation. Challenges included long-term adherence, scalability, data integration, security, and ownership. | The source is a systematic review of passive sensors in remote monitoring that explicitly mentions detecting acute events such as heart failure decompensation and lists long-term adherence, scalability, and data integration among the challenges. |


###### Table 3c: Uncited Claims
*No claims found*



#### 📊 Run 3: Cancer Detection (DeepSeek V4 Flash)

##### Stage 1: Search Query Intent Coverage Evidence Table
Methodology: Verifies if the user intents are addressed by generated queries. Prompt: `02_prompts/03_stage1_intent_coverage.md`.

*Skipped (missing intent coverage logs)*


##### Stage 2a: Directional Alignment Evidence Table
Methodology: Verifies if the user intents are addressed in the report outline without topic drift. Prompt: `02_prompts/04_stage2_directional.md`.

*Skipped (missing directional alignment logs)*


##### Stage 2b: Data Extraction Accuracy Evidence Table
Methodology: Audits intermediate spreadsheet values against source abstract text. Prompt: `02_prompts/05_verify_data_extraction.md`.

*Skipped (missing data extraction logs or schema mismatch)*


##### Stage 2c: Synthesis Faithfulness Evidence Table
Methodology: Verifies if synthesized report claims are faithful to the spreadsheet rows. Prompt: `02_prompts/06_verify_synthesis_faithfulness.md`.

*Skipped (missing synthesis faithfulness logs or schema mismatch)*


##### Stage 3: Cited Claim Grounding Evidence Tables
Methodology: Extracts report claims and grounds them against cited papers. Prompt: `02_prompts/08_stage3_ground_claim.md`.

###### Table 3a: Factual Hallucinations (Unsupported, Overstated, or Contradicted Claims)
| Report Claim | Citations | Verdict | Source Paper Says (Verbatim Abstract) | Contrast Evidence / Hallucination Detail |
| :--- | :--- | :---: | :--- | :--- |
| CNN ensemble applied to prostate mpMRI achieved median AUC of 0.88. | [4] | UNSUPPORTED | AI-based technologies achieved a median AUC-ROC of 0.88 (range 0.70–0.93) | The source states that AI-based technologies achieved a median AUC-ROC of 0.88, but it does not specify that a CNN ensemble was used or that this result is specifically from a CNN ensemble applied to prostate mpMRI. |
| CNN ensemble applied to prostate mpMRI achieved median sensitivity of 86%. | [4] | UNSUPPORTED | AI-based technologies achieved median sensitivity of 0.86. | The source does not mention CNN ensemble; it only reports a median sensitivity of 86% for AI-based technologies broadly. |
| Ensemble ML on blood cfDNA/methylation achieved AUC up to 0.993 for multi-cancer detection. | [11] | UNSUPPORTED | The maximum values of the assessment indicators such as ... area under the curve (AUC) in included studies were ... 0.9929 | The source reports a maximum AUC of 0.9929 across all studies but does not mention 'Ensemble ML on blood cfDNA/methylation' or 'multi-cancer detection' specifically. |
| Genomic/omics AI meta-analysis reported AUC range approximately 0.90–0.993. | [11] | UNSUPPORTED | The maximum values of the assessment indicators such as ... area under the curve (AUC) in included studies were ... 0.9929 | The source reports a maximum AUC of 0.9929, not a range of approximately 0.90–0.993 as claimed. |
| Small cohort sizes and risk of overfitting are concerns in high-performance genomics AI reports. | [10], [11] | UNSUPPORTED | Source 10 discusses lack of large-scale clinical validation studies for MCED tests; Source 11 reviews AI techniques in precision medicine without addressing cohort sizes or overfitting. | Neither source mentions small cohort sizes or risk of overfitting in high-performance genomics AI reports. |
| Assay standardization challenges exist across platforms and laboratories for genomics-based AI. | [10] | UNSUPPORTED | The source discusses MCED tests combining molecular analysis with AI but does not address assay standardization challenges. | The source does not mention assay standardization challenges across platforms and laboratories for genomics-based AI. |
| SHAP-guided random forest and CNN fusion of CT imaging and gene expression for lung cancer achieved AUC 0.963. | [7] | OVERSTATED | The fusion of genomic and imaging modalities significantly enhances classification performance, achieving an AUC of 96.3% | The source reports an AUC of 96.3%, not 0.963, and the claim uses a different numeric format (0.963) which is equivalent but the source does not mention 'SHAP-guided random forest and CNN fusion' as the method; it describes a multi-modal framework with Random Forest and CNN+VAE, and the claim's phrasing is more specific and less qualified than the source. |
| Integrated heterogeneous data types, missing modalities, and multi-site alignment are challenges for multimodal AI. | [12], [14] | UNSUPPORTED | The sources present frameworks that fuse imaging, clinical, and demographic data (LungGuard) or histopathological images, genomic profiles, and clinical information (cervical cancer framework), and mention multi-centre data but not as a challenge. | The sources describe multimodal AI systems and their successes but do not discuss challenges such as integrated heterogeneous data types, missing modalities, or multi-site alignment. |
| Most gains of multimodal AI are demonstrated on retrospective datasets. | [12], [13] | UNSUPPORTED | The lung cancer source mentions training on a multi-centre dataset and future work in prospective cohorts; the cervical cancer source describes using cohorts but does not specify retrospective or prospective. | Neither source discusses the proportion of multimodal AI gains demonstrated on retrospective versus prospective datasets; they only describe their own studies. |
| Most high-performing AI models are validated retrospectively; prospective randomized clinical trials are rare. | [10], [12], [4] | UNSUPPORTED | Source [12] implies its own model validation was not yet prospective (future work aims at prospective cohorts), and source [4] concludes that 'large-scale prospective trials are required to validate clinical integration.' | The source abstracts do not state that most high-performing AI models are validated retrospectively, nor do they explicitly claim that prospective randomized clinical trials are rare; they only note a need for large-scale prospective trials, which does not directly confirm the claim. |
| Small cohorts relative to model complexity inflate reported performance, especially in genomics. | [10], [11] | UNSUPPORTED | The sources focus on MCED tests and a systematic review of AI in precision medicine, without addressing cohort size or performance inflation. | Neither source discusses small cohorts relative to model complexity or inflated performance, especially in genomics. |
| Models trained on single-institution data often underperform on external datasets. | [3], [4] | UNSUPPORTED | Source 3 discusses generalization from UK to USA, and Source 4 mentions methodological heterogeneity restricting generalizability, but neither directly addresses the claim. | The source texts discuss AI performance in breast cancer screening and prostate cancer detection, but do not mention training on single-institution data or underperformance on external datasets. |
| False-positive rates in CT lung nodule detection and mammography remain clinically significant. | [2], [6] | UNSUPPORTED | For CT: 'specificity remained variable'; for mammography: no mention of false-positive rates. | The source for CT lung nodule detection mentions variable specificity but does not state that false-positive rates are clinically significant, and the mammography source does not discuss false-positive rates. |
| Tissue-of-origin misclassification in MCED tests is a key barrier to clinical deployment. | [10] | UNSUPPORTED | The abstract lists 'major factors which are preventing clinical implementation' but does not specify tissue-of-origin misclassification. | The source does not mention tissue-of-origin misclassification as a barrier; it only notes that large-scale clinical validation studies are lacking. |
| Requiring paired, synchronized data from multiple modalities reduces available training datasets and complicates real-world deployment. | [12], [14] | UNSUPPORTED | Both abstracts focus on the benefits and performance of multimodal fusion, with no mention of data pairing limitations or deployment challenges. | Neither source discusses any reduction in available training datasets or complications in real-world deployment caused by requiring paired, synchronized multimodal data. |
| The NHS-Galleri trial in the UK is evaluating blood-based MCED tests in population screening contexts. | [10] | UNSUPPORTED | The abstract discusses MCED tests generally and notes that large-scale clinical validation studies are still lacking, but does not reference any specific trial. | The source text does not mention the NHS-Galleri trial or any specific UK trial evaluating blood-based MCED tests in population screening contexts. |
| SHAP values, GradCAM, and attention visualization are increasingly integrated into cancer detection pipelines. | [7] | UNSUPPORTED | Grad-CAM and SHAP techniques validate salient radiomic features; no mention of attention visualization or increasing integration. | The source describes a single study using SHAP and Grad-CAM but does not mention attention visualization or state that these methods are increasingly integrated into cancer detection pipelines. |


###### Table 3b: Grounded Faithful Claims (Supported Claims)
| Report Claim | Citations | Source Paper Says (Verbatim) | Grounding Proof |
| :--- | :--- | :--- | :--- |
| Large-scale deployment studies and head-to-head comparisons with radiologists have been reported, particularly in breast and lung cancer screening. | [1], [2], [3] | Source 2: 'This systematic review compares the diagnostic accuracy... of AI algorithms and radiologists in identifying lung nodules'; Source 3: 'an AI system... outperformed all of the human readers'. | Source 2 is a systematic review comparing AI and radiologists for lung nodule detection, and Source 3 evaluates an AI system for breast cancer screening that outperforms radiologists, directly supporting the claim of head-to-head comparisons in both cancer types. |
| Breast cancer detection using mammography plus ultrasound multimodal imaging with deep learning fusion achieved an AUC of 0.968. | [5] | AUC (0.968 (95% CI:0.947-0.989)) | The source explicitly states that the multimodal classification model achieved an AUC of 0.968 (95% CI:0.947-0.989), which matches the claim. |
| Breast cancer detection using mammography plus ultrasound multimodal imaging with deep learning fusion achieved a specificity of 96.41%. | [5] | Experimental results demonstrate that the multimodal classification model outperforms single-modal models in terms of specificity (96.41% (95% CI:93.10%-99.72%)) | The source explicitly states that the multimodal classification model achieved a specificity of 96.41%. |
| AI CAD applied to longitudinal screening mammography achieved AUC of 0.63–0.67. | [6] | For all time points combined, excluding screen detection, the area under the receiver operating characteristic curve (AUC) ranged from 0.63 to 0.67 for the three AI CAD systems | The source states that for all time points combined, excluding screen detection, the AUC ranged from 0.63 to 0.67 for the three AI CAD systems. |
| AI CAD applied to longitudinal screening mammography achieved sensitivity of 13–25% for pre-diagnostic detection. | [6] | At 90% specificity, the proportion of cancers potentially flagged by AI-1, AI-2, and AI-3 was 12.7%, 13.8%, and 17.0% at 10 years before diagnosis; 19.0%, 19.6%, and 19.7% at 6 years; and 24.2%, 23.3%, and 25.2% at 4 years. | The source reports proportions of cancers flagged at 90% specificity for various years before diagnosis, ranging from 12.7% to 25.2%, which matches the claim's 13–25% sensitivity range for pre-diagnostic detection. |
| AI CAD applied to longitudinal screening mammography achieved specificity fixed at 90%. | [6] | At 90% specificity, the proportion of cancers potentially flagged by AI-1, AI-2, and AI-3 was ... | The source explicitly states that the AI CAD systems were evaluated at a fixed 90% specificity, reporting proportions of cancers flagged at that threshold. |
| CNN ensemble applied to prostate mpMRI achieved median specificity of 83%. | [4] | AI-based technologies achieved a median AUC-ROC of 0.88 (range 0.70–0.93), with median sensitivity and specificity of 0.86 and 0.83, respectively. | The source states that AI-based technologies achieved a median specificity of 0.83, which directly matches the claim's median specificity of 83%. |
| CNN-based lung CT nodule detection improved sensitivity compared to baseline. | [2] | AI models achieved higher sensitivity, especially with nodules <6mm | The source states that AI models, which include CNNs, achieved higher sensitivity in lung nodule detection, directly supporting the claim of improvement over baseline. |
| Deep learning mammography for international breast screening was non-inferior to radiologists. | [3] | the AI system maintained non-inferior performance and reduced the workload of the second reader by 88% | The source states that in a simulation of double-reading, the AI system maintained non-inferior performance compared to radiologists, and the evaluation used data from the UK and USA, supporting the claim of non-inferiority for international breast screening. |
| Deep learning mammography reduced reader workload. | [3] | the AI system maintained non-inferior performance and reduced the workload of the second reader by 88% | The source explicitly states that the AI system reduced the workload of the second reader by 88% in a simulation of the double-reading process. |
| Direct comparison with radiologist performance is available for imaging-based AI. | [3] | In an independent study of six radiologists, the AI system outperformed all of the human readers | The source explicitly states that the AI system outperformed all six radiologists in an independent study, providing a direct comparison with radiologist performance. |
| Dataset heterogeneity across scanners, institutions, and annotation protocols reduces generalizability of imaging-based AI. | [4], [2] | methodological heterogeneity and limited standardization restrict generalizability | The first source explicitly states that 'methodological heterogeneity and limited standardization restrict generalizability', which directly supports the claim about dataset heterogeneity reducing generalizability. |
| False positives remain a persistent challenge in imaging-based AI, leading to specificity variability. | [2], [6] | AI models achieved higher sensitivity... however, specificity remained variable. | The first source states that AI models achieved higher sensitivity but 'specificity remained variable', which directly supports the claim that false positives remain a challenge leading to specificity variability. |
| There is limited prospective validation of imaging-based AI in real-world screening workflows. | [4], [3] | Prostate review: 'Large-scale prospective trials are required to validate clinical integration.' Breast paper: 'paves the way for clinical trials to improve the accuracy and efficiency of breast cancer screening.' | Both sources indicate that prospective validation in real-world screening is lacking: the prostate review calls for large-scale prospective trials, and the breast cancer study is retrospective and paves the way for future clinical trials. |
| Genomics-based AI approaches are promising for multi-cancer early detection because they are non-invasive and cancer-type agnostic. | [10] | MCED tests combine molecular analysis of tumor-related markers in body fluids with AI to simultaneously detect a variety of cancers, are minimally invasive, and depict great potential for clinical application. | The source describes MCED tests as minimally invasive and capable of detecting multiple cancers simultaneously, which aligns with the claim's 'non-invasive' and 'cancer-type agnostic' attributes, and states they have 'great potential'. |
| ML spectral classifier on SERS serum artificial nose achieved 100% sensitivity for NSCLC detection. | [9] | Using an optimized multireceptor array, the model achieves 100% sensitivity at 98% specificity | The source explicitly states that the model achieves 100% sensitivity for NSCLC detection. |
| ML spectral classifier on SERS serum artificial nose achieved 98% specificity for NSCLC detection. | [9] | the model achieves 100% sensitivity at 98% specificity | The source explicitly states that the model achieves 98% specificity for NSCLC detection. |
| 1D-CNN + LSTM on urine proteomics achieved AUC 0.98 for pancreatic cancer detection. | [8] | the area under curve (AUC) of 98% | The source explicitly states that the 1D-CNN + LSTM model achieved an AUC of 98% for diagnosing pancreatic cancer using urine biomarkers. |
| 1D-CNN + LSTM on urine proteomics achieved 97% accuracy for pancreatic cancer detection. | [8] | our proposed 1-D CNN + LSTM model achieved the best accuracy score of 97% | The source explicitly states that the 1-D CNN + LSTM model achieved 97% accuracy for diagnosing pancreatic cancers using urine biomarkers. |
| Most blood-based multi-cancer early detection tests are not yet clinically validated at population scale. | [10] | large-scale clinical validation studies are still lacking | The source states that 'large-scale clinical validation studies are still lacking' for MCED tests, which directly supports the claim that most are not yet clinically validated at population scale. |
| Multimodal AI systems consistently demonstrate performance gains over single-modality approaches. | [7], [12], [13], [14] | The fusion of genomic and imaging modalities significantly enhances classification performance (AUC 96.3% vs. 91.8% imaging alone and 89.7% gene expression alone); multimodal solution reaches up to AUC 0.96 and is significantly better than unimodal; the model registers a 95.88% diagnostic accuracy and AUC of 0.98, highlighting improvements. | Each cited source reports that multimodal fusion outperforms single-modality approaches, with quantitative results showing higher AUC and accuracy for the multimodal models. |
| Semi-supervised deep fusion of histopathology, genomics, and clinical data for cervical cancer achieved AUC 0.98. | [14] | its Area Under the Curve (AUC) of 0.98 is testament to its high discriminative ability. | The source explicitly states that the model achieved an AUC of 0.98. |
| Semi-supervised deep fusion of histopathology, genomics, and clinical data for cervical cancer achieved sensitivity 96%. | [14] | the model registering a ... sensitivity of 96% | The source explicitly states that the model achieved a sensitivity of 96%, matching the claim exactly. |
| Semi-supervised deep fusion of histopathology, genomics, and clinical data for cervical cancer achieved specificity 94%. | [14] | the model registering a 95.88% diagnostic accuracy, sensitivity of 96%, and specificity of 94% | The source explicitly states that the model achieved a specificity of 94%. |
| LungGuard 3D-CNN fusion of low-dose CT, biomarkers, and demographics for lung cancer achieved AUC 0.96. | [12] | Preliminary results show that LungGuard achieves AUC ≈ 0.96, sensitivity ≈ 92%, specificity ≈ 90% in early-stage (I & II) lung cancer detection | The source explicitly states that LungGuard achieves AUC ≈ 0.96 in early-stage lung cancer detection. |
| LungGuard 3D-CNN fusion of low-dose CT, biomarkers, and demographics for lung cancer achieved sensitivity approximately 92%. | [12] | Preliminary results show that LungGuard achieves AUC ≈ 0.96, sensitivity ≈ 92%, specificity ≈ 90% in early-stage (I & II) lung cancer detection | The source explicitly states that LungGuard achieves sensitivity approximately 92% in early-stage lung cancer detection. |
| LungGuard 3D-CNN fusion of low-dose CT, biomarkers, and demographics for lung cancer achieved specificity approximately 90%. | [12] | Preliminary results show that LungGuard achieves ... specificity ≈ 90% in early-stage (I & II) lung cancer detection | The source explicitly states that LungGuard achieves specificity ≈ 90% in early-stage lung cancer detection. |
| Multimodal AI using visual, genomic, and clinical features for cervical cancer achieved high performance. | [13] | The multimodal solution reached up to AUC 0.96 and was significantly better than unimodal. | The source explicitly states that the multimodal AI solution reached an AUC of 0.96, which indicates high performance. |
| SHAP and attention maps enable clinical interpretability in multimodal AI. | [7] | Grad-CAM and SHAP techniques validate salient radiomic features... By combining high predictive accuracy with interpretability across data types, the proposed framework advances radiogenomic lung cancer detection while setting a precedent for deploying trustworthy AI systems in precision oncology. | The source explicitly states that SHAP and Grad-CAM techniques validate salient radiomic features and that the framework combines high predictive accuracy with interpretability across data types, which directly supports the claim that SHAP and attention maps enable clinical interpretability in multimodal AI. |
| Imaging alone (CT-CNN) for lung cancer detection achieved AUC of 91.8%. | [7] | achieving an AUC of 96.3%, compared to 91.8% with imaging alone and 89.7% with gene expression alone. | The source explicitly states that imaging alone achieved an AUC of 91.8%. |
| Genomics alone (gene expression RF) for lung cancer detection achieved AUC of 89.7%. | [7] | The fusion of genomic and imaging modalities significantly enhances classification performance, achieving an AUC of 96.3%, compared to 91.8% with imaging alone and 89.7% with gene expression alone. | The source explicitly states that gene expression alone achieved an AUC of 89.7%. |
| Multimodal fusion for lung cancer detection achieved AUC of 96.3%. | [7] | The fusion of genomic and imaging modalities significantly enhances classification performance, achieving an AUC of 96.3% | The source explicitly states that the fusion of genomic and imaging modalities achieved an AUC of 96.3%. |
| Fusion provided a +4.5 percentage point gain over the best single modality in lung radiogenomics. | [7] | The fusion of genomic and imaging modalities significantly enhances classification performance, achieving an AUC of 96.3%, compared to 91.8% with imaging alone and 89.7% with gene expression alone. | The source states fusion achieved 96.3% AUC versus 91.8% for imaging alone, a difference of 4.5 percentage points. |


###### Table 3c: Uncited Claims
| Report Claim | Verdict | Reasoning |
| :--- | :---: | :--- |
| Regulatory-cleared AI tools exist, including FDA-cleared CAD systems. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging-based AI performance degrades for rare cancers with limited training data. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Very high AUCs (>0.99) in genomics studies often reflect small, homogeneous cohorts with potential overfitting. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics-based AI can detect molecular alterations before imaging-detectable lesions. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Tissue-of-origin prediction accuracy in genomics-based AI varies, and misclassification can misdirect workup. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal AI systems can handle missing modalities with imputation or masking strategies. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Requiring paired imaging and molecular data significantly reduces available training cohorts for multimodal AI. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| 3D CNN fusion pipelines require substantial GPU resources. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging-based AI achieved best AUC of 0.968. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging-based AI achieved best sensitivity of 86% (median) for prostate cancer. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging-based AI achieved best specificity of 96.41% for breast imaging. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging-based AI has validation scale large, at population-scale. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics-based AI achieved best AUC of 0.98–0.993. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics-based AI achieved best sensitivity of 100% for NSCLC SERS. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics-based AI achieved best specificity of 98% for NSCLC SERS. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics-based AI validation scale is small to medium cohorts. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal fusion AI achieved best AUC of 0.98. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal fusion AI achieved best sensitivity of 96% for cervical cancer. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal fusion AI achieved best specificity of 94% for cervical cancer. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal fusion AI validation scale is medium, multi-centre. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging AUC range is 0.63–0.97. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics AUC range is 0.90–0.993. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal AUC range is 0.96–0.98. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging sensitivity range is 13–100% (task-dependent). | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics sensitivity range is high in small cohorts. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal sensitivity range is approximately 90–96%. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging specificity range is 83–96%. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics specificity range is 83–98%. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal specificity range is approximately 90–94%. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging clinical maturity is four out of five stars. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics clinical maturity is two out of five stars. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal clinical maturity is three out of five stars. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging invasiveness is non-invasive. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics invasiveness is minimally invasive. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal invasiveness varies. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging data requirements are imaging archives. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics data requirements are biobank plus assay data. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal data requirements are both imaging and genomic data plus clinical data. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging scalability is high. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics scalability is medium. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal scalability is low to medium. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging explainability is medium using GradCAM. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics explainability is low to medium. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal explainability is medium using SHAP and attention. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging regulatory approval is partial with FDA-cleared CAD systems. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics regulatory approval is limited. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal regulatory approval is none yet. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Few AI-based cancer screening tools have achieved broad clinical approval. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Large-scale pre-trained vision transformers such as CONCH and UNI are trained on millions of pathology images and enable zero-shot and few-shot cancer detection. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Federated learning enables training on distributed hospital datasets without sharing raw patient data. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Post-market surveillance of FDA-cleared AI tools in mammography and lung CT screening is generating real-world performance data. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |



## Production Release Readiness Delta Analysis

The target release gates vs. the actual metrics computed by the evaluator are contrasted in the table below:

| Production Release Gate | Required Gate | Run 1 (DeepSeek) | Run 2 (MiniMax) | Run 3 (Cancer) | Gate Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Stage 1: Intent Coverage** | $\ge 98.0\%$ | 100.0% (3/3) | 100.0% (5/5) | *Skipped* | **PASS** |
| **Stage 2: Data Extraction Accuracy** | $\ge 95.0\%$ | 53.3% (8/15) | *Skipped* | *Skipped* | **FAIL** |
| **Stage 3: Cited Grounding Rate** | $\ge 90.0\%$ | 28.4% (27/95) | 13.8% (4/29) | 66.0% (33/50) | **FAIL** |

### Release Delta & Action Plan
To transition the report-writing pipeline from **Do Not Ship** to **Production-Ready**, the engineering team must resolve the following three gaps:
1. **Transition to High-Reasoning Frontier Models:** The low grounding rates (28.4% for DeepSeek Flash, 13.8% for MiniMax) demonstrate that Flash-tier writing models are highly prone to hallucinating facts and references. The report generation model must be upgraded to a frontier model (such as Claude 3.5 Sonnet) operating at temperature 0.
2. **Add Schemas and Validation Filters to Data Extraction:** In Run 1, the data extraction accuracy of 53.3% acts as the primary data corruption vector. When compilation prompts ask the writing model to summarize abstract text into criteria columns, the model frequently fabricates specific conditions (COPD, diabetes) or sample sizes. Enforcing rigid schemas and structured extraction checks at the spreadsheet boundary will prevent these errors from propagating into the final text synthesis.
3. **Audit and Mitigate Uncited Claims:** The cancer detection report (Run 3) has **51 out of 101 claims (50.5%) uncited**. To guarantee usability, the report writer must be constrained to only assert facts that are traceably linked to a cited paper ID, and any uncited statistical assertion must be rejected by a validation pass prior to presentation.

---

## Production Realities: What Actually Happens vs. Ideal Design

Analyzing the actual codebase execution (`run_evaluator.py`) reveals a series of compromises, hardcodings, and fragile assumptions that diverge from the ideal pipeline design described in theory. This section details these operational realities to ensure absolute clarity for presentation and debugging purposes:

### 1. The Hardcoded Column Constraint (Why Run 2 Skipped Stage 2b & 2c)
* **The Ideal:** The evaluator should dynamically identify and evaluate the consolidated table columns for any research topic.
* **The Reality:** The column parsing in `run_evaluator.py` is hardcoded to specific column headers from the wearables trial:
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
   Before writing python scripts, the core evaluation logic was written in plain markdown prompt templates in the `02_prompts/` directory. This isolates the evaluation rules from execution plumbing:
   * [00_classify_files.md](file:///Users/office/Desktop/sci%20space/02_prompts/00_classify_files.md)
   * [01_clean_search_queries.md](file:///Users/office/Desktop/sci%20space/02_prompts/01_clean_search_queries.md)
   * [02_extract_intents.md](file:///Users/office/Desktop/sci%20space/02_prompts/02_extract_intents.md)
   * [03_stage1_intent_coverage.md](file:///Users/office/Desktop/sci%20space/02_prompts/03_stage1_intent_coverage.md)
   * [04_stage2_directional.md](file:///Users/office/Desktop/sci%20space/02_prompts/04_stage2_directional.md)
   * [05_verify_data_extraction.md](file:///Users/office/Desktop/sci%20space/02_prompts/05_verify_data_extraction.md)
   * [06_verify_synthesis_faithfulness.md](file:///Users/office/Desktop/sci%20space/02_prompts/06_verify_synthesis_faithfulness.md)
   * [07_stage3_extract_claims.md](file:///Users/office/Desktop/sci%20space/02_prompts/07_stage3_extract_claims.md)
   * [08_stage3_ground_claim.md](file:///Users/office/Desktop/sci%20space/02_prompts/08_stage3_ground_claim.md)
   * [09_prepare_input_folder.md](file:///Users/office/Desktop/sci%20space/02_prompts/09_prepare_input_folder.md)

2. **Phase 2: Runner Core ([run_evaluator.py](file:///Users/office/Desktop/sci%20space/01_code/run_evaluator.py))**:
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
  03_runs/run_1_wearables_deepseek/
  ├── user_query.txt          <-- Original user query
  ├── search_queries.txt      <-- Raw log of channel searches
  ├── search_queries.json     <-- Pre-cleaned channel/query pairs
  ├── intermediate_report.md  <-- Insights report
  ├── final_report.md         <-- Final cited report
  ├── scorecard.md            <-- Output scorecard generated by the runner
  ├── detailed_log.json       <-- Detailed JSON results log generated by the runner
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

### Appendix C: SciSpace Evals Workflow

Use this guide to quickly copy and paste formatting instructions into a coding agent when evaluating new SciSpace runs. This keeps all inputs and outputs organized under sequentially numbered run names under `03_runs/` so nothing is ever overwritten.

#### 📁 Workspace Directory Structure
