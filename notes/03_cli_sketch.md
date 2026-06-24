# CLI: How It Works

## Input

The runner gets a **folder** with all files from one SciSpace run. File names are not standardised — the runner infers which file is which.

```bash
python eval.py ./run_001/
```

Example folder contents:
```
run_001/
  user_query.txt
  search_queries_log.txt
  wearable_insights.md
  wearable_health_devices_chronic_disease_report.md
```

## What the runner does

```
Step 0:  Classify & reformat inputs
Step 1:  Stage 1 eval (query hallucination)
Step 2:  Stage 2 eval (directional faithfulness)
Step 3:  Stage 3 eval (claim-level fact-checking)
Step 4:  Print scorecard
```

Each eval stage uses a prompt loaded from a separate file (see Project Structure below). This way a PM can edit and refine the eval prompts without touching the runner code.

---

## Step 0: Classify & Reformat Inputs

The runner reads all files in the folder and makes an LLM call to classify them:

```
Here are the file names and first few lines of each file in this folder:
{file_previews}

Classify each file as one of:
- user_query: the original user request
- search_queries: the log of search queries sent to databases
- intermediate_report: extracted insights or summary before the final report
- final_report: the full report with citations and references
- other: not needed for evaluation
```

Once classified, a second LLM call reformats the search queries log — extracting clean channel + query pairs from the messy log text (which includes emoji, paper counts, status messages, etc.):

```
Extract the search queries from this log.
For each, give me the channel name and the exact query string.
Ignore status messages, paper counts, and summaries.
```

After Step 0, the runner has:
- `user_query` — plain text
- `search_queries` — list of {channel, query} pairs
- `intermediate_report` — markdown text
- `final_report` — markdown text

---

## Step 1: Stage 1 Eval — Query Hallucination

**Inputs:** user_query + search_queries

**LLM calls:**
1. Extract atomic intents from user query ← uses `prompts/extract_intents.md`
2. For each search query, check which intents it covers ← uses `prompts/stage1_intent_coverage.md`

**Deterministic:** count intents covered ÷ total intents → **Intent Coverage %**

---

## Step 2: Stage 2 Eval — Directional Faithfulness

**Inputs:** user_query (same intents from Step 1) + intermediate_report

**LLM call:**
1. Check intermediary report against intents + detect drift ← uses `prompts/stage2_directional.md`

**Deterministic:** count intents addressed ÷ total intents, flag any drift → **Directional Alignment %**

---

## Step 3: Stage 3 Eval — Claim-Level Fact-Checking

**Inputs:** final_report only

**LLM call:**
1. Split report into atomic claims with citation IDs ← uses `prompts/stage3_extract_claims.md`

**Deterministic:** fetch paper content via DOI/URL links from References section.

**LLM call:**
2. For each claim (all of them, not a sample), judge against fetched source ← uses `prompts/stage3_ground_claim.md`

Labels: Supported / Unsupported / Contradicted / Overstated

**Deterministic:** count supported ÷ total verifiable → **Grounding Rate %**

> **Presentation note:** Deterministic pre-checks (phantom citations, missing DOIs, exact number mismatches) are worth highlighting in documentation as additional quality signals, but are not part of the core eval flow.

---

## Project Structure

```
scispace-evals/
  eval.py                          ← the runner
  prompts/
    extract_intents.md             ← "extract atomic intents from this query"
    stage1_intent_coverage.md      ← "which intents does this search query cover?"
    stage2_directional.md          ← "does this report align with these intents?"
    stage3_extract_claims.md       ← "split this report into atomic claims"
    stage3_ground_claim.md         ← "is this claim supported by this source?"
  output/
    scorecard.md                   ← the results
    detailed_log.json              ← every individual judgment
```

Prompts are plain markdown files. The runner reads them, fills in the variables, and sends them to the LLM. A PM can edit any prompt without touching `eval.py`.

---

## Output

The scorecard shows metrics **and** concrete evidence for every failure. Numbers alone aren't useful — you need to see *why* a metric is what it is.

```
HALLUCINATION EVAL SCORECARD
─────────────────────────────

Stage 1: Query Hallucination
  Intent Coverage ............... 80%     (4/5 intents covered)

  ✗ MISSED INTENT: "long-term health outcomes"
    No search query across any channel addressed this dimension.
    Closest query: "wearable health devices chronic disease management
    adherence accuracy" (SciSpace Full Text) — covers adherence and
    accuracy but omits long-term outcomes.


Stage 2: Directional Faithfulness
  Directional Alignment ......... 80%     (4/5 intents addressed, drift detected)

  ✗ MISSING: "long-term health outcomes"
    The intermediary report has no section or substantive content
    addressing long-term outcomes.

  ✗ DRIFT: "device market trends"
    The report includes a section on market growth projections
    which is unrelated to any user intent.


Stage 3: Claim-Level Fact-Checking
  Grounding Rate ................ 82%     (54/66 claims supported)
    - Supported ................. 54      (82%)
    - Unsupported ............... 6       (9%)
    - Contradicted .............. 1       (2%)
    - Overstated ................ 5       (8%)

  ✗ CONTRADICTED:
    Claim: "CGM reduced HbA1c by 0.35%"  [6]
    Source says: "WMD −0.17%"
    → Report states a larger effect than the paper reports.

  ✗ OVERSTATED (example 1 of 5):
    Claim: "Research proves wearable devices improve cardiovascular outcomes" [27]
    Source says: "limited and inconsistent effects on cardiometabolic risk markers"
    → Report presents as proven what the source calls inconsistent.

  ✗ UNSUPPORTED (example 1 of 6):
    Claim: "Wearable adoption increased 40% year-over-year" [14]
    Source: Paper discusses clinical effectiveness, not adoption rates.
    → No basis for this claim in the cited paper.
```

Every failure comes with: what the report said, what the source said (or what was expected), and why it's a problem. The LLM judge generates this evidence as part of its classification — it's not extra work.

---

## In summary, the runner is:

1. A few LLM calls to **classify and clean** the input files
2. A few LLM calls using **external prompt files** to run each eval stage — each producing verdicts **with evidence**
3. Arithmetic to **compute the metrics**
4. A **scorecard with evidence** printed and saved

The judge LLM is configured separately — not hardcoded.
