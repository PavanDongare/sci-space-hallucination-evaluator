# SciSpace Hallucination Evaluator: Correct System Design

## 1. What The Evaluator Does

The evaluator audits one completed SciSpace research run.

SciSpace has already done the work:

```text
user query
-> generated database queries
-> retrieved papers/source CSVs
-> generated combined/intermediate files
-> generated final report
```

The evaluator does not write the report. It checks whether the generated parts are faithful to the user query and to the retrieved source evidence.

There are two main questions:

```text
1. Did SciSpace search for the right thing?
2. Did SciSpace hallucinate while generating tables, insights, or reports?
```

## 2. Runner Input

The runner receives one folder.

Example:

```text
python3 01_code/run_evaluator.py 03_runs/run_3_cancer_detection/
```

A run folder may contain files like:

```text
user_query.txt
search_queries.txt
search_queries.json

pubmed_*.csv
scholar_*.csv
arxiv_*.csv
scispace_*.csv
scispace_fulltext_*.csv

combined_*.csv

intermediate_report.md
final_report.md
*_insights.md
*_report.md
*_Report.md

todo.md
todo.py
```

## 3. File Classification

The evaluator should classify files mostly by deterministic filename rules.

### Query/Input Files

```text
user_query.txt
search_queries.txt
search_queries.json
```

Used to check whether generated search queries covered the user's intent.

### Static Source Evidence Files

```text
pubmed_*.csv
scholar_*.csv
arxiv_*.csv
scispace_*.csv
scispace_fulltext_*.csv
```

These are treated as retrieved evidence from databases/search systems.

Common evidence fields:

```text
Paper Title
DOI
Abstract
Snippet
Relevant Excerpt
PDF Link
Paper Link
Author Names
Publication Year
```

### Generated Files To Audit

```text
combined_*.csv
*_insights.md
intermediate_report.md
*_report.md
*_Report.md
final_report.md
```

These are LLM-generated or mixed generated artifacts.

`combined_*.csv` is mixed: it contains source metadata plus generated columns like:

```text
Relevance
Performance Metrics
Key Findings and Methods
Study Design and Population
Limitations and Gaps
Neurochemical Signaling Pathways
Behavioral and Clinical Outcomes
```

So it should be audited as generated/intermediate output.

### Planner/Trace Files

```text
todo.md
todo.py
```

These are generated planner traces. They are useful for understanding the run, but usually not part of factual hallucination scoring.

## 4. Static vs Generated Distinction

The key design principle:

```text
Static files are the evidence.
Generated files are the things being evaluated.
```

Static evidence:

```text
pubmed_*.csv
scholar_*.csv
arxiv_*.csv
scispace_*.csv
scispace_fulltext_*.csv
```

Generated/hallucination targets:

```text
combined_*.csv
*_insights.md
*_report.md
final_report.md
intermediate_report.md
```

`user_query.txt` and `search_queries.*` are separate: they are used for query evaluation, not source fact-checking.

## 5. Stage 1: Query Coverage

Purpose:

```text
Check whether generated database queries preserved the user's request.
```

Files used:

```text
user_query.txt
search_queries.txt
search_queries.json
```

Prompts used:

```text
02_prompts/02_extract_intents.md
02_prompts/01_clean_search_queries.md
02_prompts/03_stage1_intent_coverage.md
```

Process:

```text
1. Read user_query.txt.
2. Extract atomic user intents.
3. Read search_queries.json if present.
4. If JSON is missing, clean search_queries.txt into channel/query pairs.
5. Check whether at least one generated query covers each user intent.
```

Metric:

```text
Intent Coverage = covered intents / total intents
```

Example:

```text
User asks for cancer detection across imaging, genomics, multimodal methods using AUC/sensitivity/specificity.

Generated queries should include:
- imaging
- genomics
- multimodal
- AUC
- sensitivity
- specificity
```

## 6. Stage 2: Evidence Registry

Purpose:

```text
Build the source evidence base used for fact checking.
```

Files used:

```text
pubmed_*.csv
scholar_*.csv
arxiv_*.csv
scispace_*.csv
scispace_fulltext_*.csv
```

No LLM is needed here.

The runner creates a paper registry:

```text
paper_id
title
doi
authors
abstract
snippet
relevant_excerpt
pdf_link
source_file
source_database
```

For each paper, the registry should preserve all available evidence levels:

```text
1. full_text, if a PDF/full-text link can be fetched or already exists
2. relevant_excerpt, usually from scispace_fulltext_*.csv
3. abstract
4. snippet
5. title/reference metadata only
```

Grounding stages should always use the strongest available evidence. If full text is available, use full text chunks for claim validation. If full text is not available, fall back to relevant excerpts, then abstracts, then snippets.

Metrics:

```text
Evidence Records Count
DOI Coverage
Abstract Coverage
PDF Link Coverage
Excerpt Coverage
Full Text Coverage
```

This stage answers:

```text
How much usable source evidence do we have?
```

## 7. Stage 3: Combined CSV Grounding

Purpose:

```text
Check whether generated cells in combined_*.csv are supported by the paper evidence.
```

Files used:

```text
combined_*.csv
static evidence registry
```

Evidence used for each generated cell:

```text
1. same-row paper full text chunks, if available
2. same-row relevant excerpt
3. same-row abstract
4. same-row snippet/title metadata
```

Prompt used:

```text
02_prompts/05_verify_data_extraction.md
```

Correct generic behavior:

```text
Do not hardcode columns.
```

Instead:

```text
Metadata/source columns are static:
Paper Title, DOI, Abstract, PDF Link, Paper Link, Author Names, Publication Year, etc.

Every other non-empty column is generated and should be checked.
```

Examples of generated columns:

```text
Relevance
Performance Metrics
Key Findings and Methods
Study Design and Model Systems
Behavioral and Clinical Outcomes
```

Metric:

```text
Generated Cell Grounding Rate = supported generated cells / checked generated cells
```

The detailed log should include evidence scope for each verdict:

```text
full_text
relevant_excerpt
abstract
snippet
metadata_only
```

This replaces the old schema-specific check.

## 8. Stage 4: Intermediate Markdown Grounding

Purpose:

```text
Check generated insight/intermediate markdown files for hallucinated claims.
```

Files used:

```text
*_insights.md
intermediate_report.md
combined_*.csv
static evidence registry
```

Evidence used for each intermediate claim:

```text
1. cited paper full text chunks, if available
2. cited paper relevant excerpt
3. cited paper abstract
4. cited paper snippet/title metadata
```

Prompts used:

```text
02_prompts/07_stage3_extract_claims.md
02_prompts/08_stage3_ground_claim.md
```

Process:

```text
1. Extract factual claims from markdown.
2. Preserve citation IDs like [1], [2].
3. Resolve citations.
4. Check claims against source evidence.
```

Citation resolution:

```text
If markdown has References section:
  use references.

If markdown has citation IDs but no References section:
  map [n] to row n in combined_*.csv.

If no citation/source can be resolved:
  mark provenance_missing.
```

Metrics:

```text
Intermediate Claim Grounding Rate
Intermediate Provenance Coverage
Intermediate Uncited Claim Rate
Intermediate Full-Text Grounding Coverage
Intermediate Abstract-Only Grounding Coverage
```

## 9. Stage 5: Final Report Grounding

Purpose:

```text
Check whether the final report's factual claims are supported by cited sources.
```

Files used:

```text
final_report.md
*_report.md
*_Report.md
combined_*.csv
static evidence registry
```

Evidence used for each final report claim:

```text
1. cited paper full text chunks, if available
2. cited paper relevant excerpt
3. cited paper abstract
4. cited paper snippet/title metadata
```

Prompts used:

```text
02_prompts/07_stage3_extract_claims.md
02_prompts/08_stage3_ground_claim.md
```

Process:

```text
1. Extract atomic factual claims.
2. Extract citation IDs.
3. Parse References section if present.
4. Resolve each citation to a paper.
5. Retrieve source evidence from registry.
6. Judge support.
```

Possible verdicts:

```text
supported
unsupported
overstated
contradicted
uncited
not_verifiable
```

Metrics:

```text
Final Claim Reliability = supported claims / all non-common factual claims

Cited Grounding Rate = supported cited claims / cited verifiable claims

Uncited Claim Rate = uncited factual claims / total claims

Not Verifiable Rate = unresolved claims / total claims

Final Full-Text Grounding Coverage = final claims checked with full text / final claims checked

Final Abstract-Only Grounding Coverage = final claims checked only with abstract/snippet/excerpt / final claims checked
```

## 10. Stage 6: Full-Text Grounding Policy

Purpose:

```text
Define exactly which evidence source is used for intermediate and final claim validation.
```

Files/fields used:

```text
PDF Link
Relevant Excerpt
Abstract
Snippet
```

### Intermediate Artifacts

For intermediate generated artifacts, such as `combined_*.csv`, `*_insights.md`, and `intermediate_report.md`, the evaluator should use the best evidence already available in the run folder first.

```text
Evidence priority for intermediate artifacts:
1. relevant_excerpt from scispace_fulltext_*.csv
2. abstract
3. snippet
4. full text, only when the excerpt/abstract is insufficient or missing
5. metadata only, only as a last resort
```

Reason:

```text
Intermediate files are closer to the retrieval/extraction phase. In many runs, scispace_fulltext_*.csv already contains text-search excerpts from full papers, so forcing full-PDF processing for every intermediate cell can be expensive and redundant.
```

### Final Report

For final report grounding, full-text grounding is required whenever a cited source has a usable PDF/full-text link.

```text
Evidence priority for final report claims:
1. cited paper full text chunks, fetched/extracted from PDF Link or full-text source
2. relevant_excerpt from scispace_fulltext_*.csv, only if full text cannot be fetched/extracted
3. abstract, only if no full text or relevant excerpt is available
4. snippet, only if no abstract is available
5. metadata only, marked not_verifiable_for_fact_grounding
```

Concrete final-report process:

```text
1. Extract claims from final_report.md / *_report.md.
2. Resolve each claim's citation IDs to cited papers.
3. For each cited paper, try to obtain full text from PDF Link or known full-text source.
4. Extract full text.
5. Split full text into chunks.
6. Retrieve the most relevant chunks for the claim.
7. Run the grounding judge on the claim and retrieved full-text chunks.
8. If full text cannot be fetched/extracted, record full_text_status = unavailable and fall back to excerpt/abstract.
9. If only metadata is available, do not call the claim supported; mark it not_verifiable_for_fact_grounding.
```

This means final-report validation is not abstract-first. It is full-text-first.

Metrics:

```text
Full Text Availability
Full Text Grounding Coverage
Abstract-Only Grounding Coverage
Full Text Fetch Failure Rate
Excerpt Fallback Rate
Metadata-Only Not-Verifiable Rate
```

Important scorecard label:

```text
unsupported_in_abstract_only
```

is weaker than:

```text
unsupported_in_full_text
```

## 11. Final Outputs

The runner writes:

```text
scorecard.md
detailed_log.json
```

The scorecard should include:

```text
Intent Coverage
Evidence DOI Coverage
Evidence Abstract Coverage
Generated Cell Grounding Rate
Intermediate Claim Grounding Rate
Final Claim Reliability
Cited Grounding Rate
Uncited Claim Rate
Not Verifiable Rate
Full Text Coverage, if enabled
Evidence Scope Breakdown
```

## 12. Correct Mental Model

The evaluator has two jobs.

First:

```text
User query
vs
generated search queries
```

This checks retrieval direction.

Second:

```text
Generated artifacts
vs
static retrieved evidence
```

This checks hallucination.

So the complete system is:

```text
user_query.txt
  -> query intent extraction

search_queries.txt / search_queries.json
  -> query coverage check

pubmed/scholar/arxiv/scispace CSVs
  -> static evidence registry

combined_*.csv
  -> generated intermediate table grounding

*_insights.md / intermediate_report.md
  -> generated intermediate claim grounding

*_report.md / final_report.md
  -> final claim grounding
```

That is the corrected design: deterministic file classification, query coverage first, then hallucination checks over every generated artifact using the static source files as evidence.
