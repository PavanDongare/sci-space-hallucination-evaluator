# Understanding: SciSpace Hallucination Evals

## What SciSpace does

User types a query → LLM generates search queries for each database → papers are retrieved → LLM extracts insights into an intermediary report → LLM writes a final report with citations.

## Why different channels have different query formats

SciSpace searches multiple databases. Each database works differently, so the LLM adapts the query format:

| Channel | Query style | Why |
|---|---|---|
| **SciSpace (semantic)** | Natural language question | Searches over paper abstracts/summaries, which are short enough for semantic search |
| **SciSpace (full-text)** | Keywords separated by spaces | Searches over full paper PDFs — too large for semantic search, so it's a deterministic string match |
| **Google Scholar** | Boolean with AND/OR, quotes, parentheses | Google Scholar's native search syntax |
| **PubMed** | MeSH terms with boolean operators | PubMed's native medical terminology search |

This matters for Stage 1: the LLM judge must understand that all these formats are trying to do the same thing (find papers matching user intent), just in different syntaxes. A keyword string like `wearable health devices chronic disease management adherence accuracy long-term outcomes` and a natural language question like `What are the effects of wearable health devices on chronic disease management?` can both cover the same user intents.

## What inputs the CLI gets

| Input | Source | What it looks like |
|---|---|---|
| **User query** | Copy-pasted from SciSpace | Plain text |
| **Search queries log** | Copy-pasted from SciSpace's search step | Semi-structured text with channel names and queries mixed with status messages and paper counts |
| **Intermediary report** | Downloaded from SciSpace | Markdown file (e.g. `wearable_insights.md`) |
| **Final report** | Downloaded from SciSpace | Markdown file with inline citations [1]-[N] and a References section with paper titles, DOIs, and links |

The search queries log in particular will be messy — it includes things like "🔍 Searching scholarly literature...", "100 Papers", "✅ Search complete!" etc. mixed in with the actual queries. The CLI needs a cleanup step to extract just the channel + query pairs.

## Three hallucination surfaces

### Surface 1: Query Hallucination
The LLM converts the user query into database-specific search queries. Risk: queries drift from or miss user intent.
**Checked against:** the user query.

### Surface 2: Directional Faithfulness
The LLM produces intermediate results (insights report). Risk: the overall direction of the results drifts from what the user asked — wrong emphasis, missing dimensions, introduced unrelated topics.
**Checked against:** the user query.

### Surface 3: Claim-Level Fact-Checking
The final report makes specific factual claims citing specific papers. Risk: claims are fabricated, contradicted, or exaggerated relative to the cited source.
**Checked against:** the cited source papers (accessed via DOI/links in the References section).
