# Implementation Plan

## What we're building

```
scispace-evals/
  eval.py                          ← the runner
  prompts/
    classify_files.md              ← "identify which file is which"
    clean_search_queries.md        ← "extract channel + query pairs from log"
    extract_intents.md             ← "extract atomic intents from user query"
    stage1_intent_coverage.md      ← "which intents does this search query cover?"
    stage2_directional.md          ← "does this report align with these intents?"
    stage3_extract_claims.md       ← "split report into atomic claims"
    stage3_ground_claim.md         ← "is this claim supported by this source?"
  output/                          ← generated per run
    scorecard.md
    detailed_log.json
```

## Build order

### Phase 1: Prompts

Write all prompt files first. These are the core of the evaluator — the code is just plumbing.

```
1. classify_files.md
2. clean_search_queries.md
3. extract_intents.md
4. stage1_intent_coverage.md
5. stage2_directional.md
6. stage3_extract_claims.md
7. stage3_ground_claim.md
```

Each prompt is a markdown file with:
- A clear instruction
- The variables it expects (e.g. `{query}`, `{intents}`)
- The output format it should return

### Phase 2: Runner core

Build `eval.py` with this flow:

```
1. Read all files from input folder
2. LLM call: classify files (→ which is query, search log, intermediate, final)
3. LLM call: clean search queries log (→ structured channel + query pairs)
4. LLM call: extract intents from user query
5. LLM call: stage 1 — check search queries against intents
6. LLM call: stage 2 — check intermediary report against intents
7. LLM call: stage 3a — extract atomic claims from final report
8. For each claim:
   a. Fetch cited paper via DOI/URL
   b. LLM call: stage 3b — judge claim against source
9. Compute metrics
10. Generate scorecard with evidence
11. Save scorecard.md + detailed_log.json
```

The runner is simple — it reads prompts, fills in variables, calls the LLM, parses responses, and does arithmetic.

### Phase 3: Test with sample data

Run the evaluator against the sample files we already have:
- User query: "Create a report on wearable health devices..."
- Search queries: `sample search queries channel wise`
- Intermediary report: `wearable_insights.md`
- Final report: `wearable_health_devices_chronic_disease_report.md`

Verify:
- Does Step 0 correctly classify and clean the files?
- Does Stage 1 extract reasonable intents and check coverage?
- Does Stage 2 detect alignment and drift correctly?
- Does Stage 3 produce sensible claim-level judgments with evidence?
- Does the scorecard look like what we designed?

### Phase 4: Polish

- Make judge LLM configurable
- Handle edge cases (papers with no DOI, unreachable links)
- Clean up scorecard formatting
