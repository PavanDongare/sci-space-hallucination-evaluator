# SciSpace Hallucination Evaluator: Matrix-Based Design

## Core Model

Every evaluator check is represented as:

```text
LLM-generated evaluation file/content
Evidence file/content
Prompt instruction
Metric being measured
```

The evaluator should not be organized around fixed schemas. It should be organized around pairs of:

```text
LLM-generated content
vs
static/user evidence
```

The evaluator should calculate an error or hallucination rate from that comparison.

## Evaluation Matrix

| # | LLM Evaluation File / Content | Evidence File / Content | Prompt Instruction | Metric Being Measured |
|---|---|---|---|---|
| 1 | Generated Space semantic query from `search_queries.json` or `search_queries.txt` | `user_query.txt` | Identify all intents from the user query. Verify whether the generated Space semantic query covers those intents. This prompt is for semantic natural-language search. | `Space Semantic Query Hallucination = 1 - verified_intents / total_intents` |
| 2 | Generated SciSpace full-text query from `search_queries.json` or `search_queries.txt` | `user_query.txt` | From the user query, identify unique, non-repeating, high-quality string-match candidates. Verify whether the generated SciSpace full-text query sufficiently covers those candidates. This prompt is for full-text search where semantic querying is not used. | `SciSpace Full-Text Query Hallucination = 1 - covered_candidates / total_candidates` |
| 3 | Generated Google Scholar query or queries from `search_queries.json` or `search_queries.txt` | `user_query.txt` | Check whether the Google Scholar query uses `AND` / `OR` hierarchy to fulfill the user query. Each generated Google Scholar query is scored as pass `1` or fail `0`. | `Google Scholar Query Score = passed_queries / total_google_scholar_queries` |
| 4 | Generated PubMed query or queries from `search_queries.json` or `search_queries.txt` | `user_query.txt` | Check whether the PubMed query language using `AND`, `+`, `all:`, and related syntax correctly queries the user query. Each generated PubMed query is scored as pass `1` or fail `0`. | `PubMed Query Score = passed_queries / total_pubmed_queries` |
| 5 | Any generated intermediate `.md` file that is not the final report, including `*_insights.md` and `intermediate_report.md` | `user_query.txt` | Identify intents from the user query. Check whether the generated intermediate markdown file addresses each intent. Each intent can be marked `addressed`, `partial`, or `not addressed`. | `Intermediate Markdown Intent Hallucination = 1 - addressed_intent_score / total_intents` |
| 6 | Any generated intermediate `.md` file that is not the final report, including `*_insights.md` and `intermediate_report.md` | Cited/resolved paper evidence from the unified paper evidence registry | Extract unique factual claims from the intermediate markdown file. Resolve citations for each claim. Verify whether each claim is supported by its cited evidence. | `Intermediate Markdown Claim Hallucination = 1 - supported_unique_claims / total_unique_claims` |
| 7 | Generated columns inside `combined_*.csv` | Unified paper evidence registry, resolved by the row's paper identity | Identify all LLM-generated columns in `combined_*.csv`. Verify each generated cell against the resolved evidence for that same paper. | `Combined CSV Generated Column Hallucination = 1 - supported_generated_cells / total_generated_cells` |
| 8 | Final report markdown, such as `final_report.md`, `*_report.md`, or `*_Report.md` | Cited paper full text first, then fallback evidence from the unified paper evidence registry | Extract unique factual claims from the final report. Resolve citations for each claim. Visit or fetch the cited links/full text. Verify whether each claim is supported, exaggerated, or hallucinated. | `Final Report Claim Hallucination = 1 - accurately_supported_unique_claims / total_unique_claims` |

## Production Input Contract vs Assignment Data Prep

In a production/internal SciSpace setting, the evaluator should not need to guess which files are LLM-generated and which files are static evidence.

The product should pass structured inputs directly:

```text
evaluation_content: the LLM-generated artifact being evaluated
evidence_content: the static/user/source evidence used for checking
prompt: the evaluator prompt for that artifact type
metric: the formula to compute
```

In that setup, the evaluator simply iterates over the matrix rows and calculates hallucination metrics. No agentic file cleanup is needed.

The current assignment data is messier. It arrives as folders containing mixed artifacts:

```text
user_query.txt
search_queries.txt / search_queries.json
source CSVs
combined CSVs
intermediate markdown
final report markdown
planner files
```

For this assignment setting, a preprocessing adapter is needed to organize the folder into the matrix inputs:

```text
1. identify user-entered evidence, such as user_query.txt
2. identify static source evidence, such as pubmed_*.csv, scholar_*.csv, arxiv_*.csv, scispace_*.csv
3. identify LLM-generated evaluation artifacts, such as generated queries, combined_*.csv, *_insights.md, and final reports
4. build the unified paper evidence registry
```

This adapter is not the core hallucination evaluator. It is only a data-preparation layer for messy exported runs.

Production should avoid non-deterministic file cleanup where possible. If the internal system already knows which artifacts are LLM-generated, which are static evidence, and which prompt applies, those should be passed directly through APIs. That prevents cleanup mistakes from causing downstream evaluation errors.

## Data Collation Before Evaluation

Before running claim or generated-cell checks, the evaluator needs a unified paper evidence registry.

Input files for the assignment data adapter:

```text
pubmed_*.csv
scholar_*.csv
arxiv_*.csv
scispace_*.csv
scispace_fulltext_*.csv
combined_*.csv metadata columns
```

Registry fields:

```text
paper_id
doi
title
full_text
relevant_excerpts
abstract
snippet
pdf_link
citation_link
source_file
source_database
```

Deduplication goal:

```text
The same paper should resolve to one registry entry even if it appears in multiple source files.
Prefer DOI when available. If DOI is missing, use normalized title matching.
```

Evidence priority for grounding:

```text
1. full text
2. relevant excerpts
3. abstract
4. snippet
5. title
```

Title-only evidence should not support detailed factual claims. It can only support title-level claims. Otherwise, title-only evidence should be treated as unsupported or not verifiable.


## Paper Evidence Registry Details

Before combined CSV, intermediate markdown claim, or final report claim grounding, the runner must use the deduplicated paper evidence registry described above.

The registry is used by these matrix rows:

```text
combined_*.csv generated column grounding
intermediate markdown claim grounding
final report claim grounding
```

Two implementation gaps from earlier designs are explicitly avoided here:

```text
1. Do not check only abstracts when full text or relevant excerpts are available.
2. Do not assume one fixed combined CSV schema from one use case.
```

## Generated Column Resolution For Combined CSV

For `combined_*.csv`, the runner must first classify columns.

Static/source metadata columns:

```text
Paper Title
Paper Link
Publication Year
Publication Type
Publication Title
Author Names
DOI
PDF Link
Abstract
Snippet
Relevant Excerpt
```

Every other non-empty column is treated as LLM-generated and should be evaluated.

Examples of LLM-generated columns:

```text
Relevance
Performance Metrics
Key Findings and Methods
Study Design and Population
Limitations and Gaps
Neurochemical Signaling Pathways
Behavioral and Clinical Outcomes
```

The generated cell is checked against the row's resolved paper evidence using the evidence priority order.

## Markdown Claim Resolution

This applies to:

```text
*_insights.md
intermediate_report.md
final_report.md
*_report.md
*_Report.md
```

Steps:

```text
1. Extract unique factual claims.
2. Extract citation IDs attached to each claim.
3. Resolve citation IDs to papers.
4. Retrieve evidence for those papers from the unified paper evidence registry.
5. Ground the claim against the resolved evidence.
```

Citation resolution order:

```text
1. If the markdown file has a References section, resolve citations from that section.
2. If it has citation IDs but no References section, resolve citation number `[n]` to row `n` in `combined_*.csv`.
3. If neither works, mark the claim as citation_unresolved.
```

## Multi-Citation Rule

The atomic unit is the claim, not each citation.

If a claim has multiple citations, evaluate each citation's evidence separately and apply majority rule:

```text
claim_supported = supported_citations > unsupported_or_non_supporting_citations
```

Examples:

```text
3 citations, 2 support, 1 does not support -> claim supported
3 citations, 1 supports, 2 do not support -> claim not supported
2 citations, 1 supports, 1 does not support -> claim not supported because there is no supporting majority
```

This measures whether the claim is hallucinated. Citation divergence can still be logged separately, but it is not the primary hallucination metric.

## Claim Verdicts

For each claim or generated CSV cell, the evaluator can classify the result as:

```text
supported
exaggerated
hallucinated
unsupported
not_verifiable
citation_unresolved
```

Only accurately supported claims/cells count as supported in the numerator.

## Metric Conventions

Positive quality metrics:

```text
verified_intents / total_intents
covered_candidates / total_candidates
passed_queries / total_queries
supported_generated_cells / total_generated_cells
supported_unique_claims / total_unique_claims
```

Hallucination or error metrics:

```text
1 - verified_intents / total_intents
1 - covered_candidates / total_candidates
1 - passed_queries / total_queries
1 - supported_generated_cells / total_generated_cells
1 - supported_unique_claims / total_unique_claims
```

The scorecard should show both when useful, but the hallucination metric should use the `1 - ...` form.

## Explicit Non-Goals

The prompts must not be topic-specific.

They should not mention dataset topics such as cancer, ADHD, microbiome, wearables, medicine, or any run-specific content.

The prompts should only encode:

```text
1. the type of LLM-generated evaluation content
2. the evidence content it must be compared against
3. the source/query syntax or evidence priority needed to judge fairly
4. the metric output needed by the evaluator
```
