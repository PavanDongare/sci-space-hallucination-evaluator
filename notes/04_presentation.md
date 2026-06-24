# Presentation: SciSpace Hallucination Evals

---

## Slide 1: The Question

```
┌─────────────────────────────────────────────┐
│                                             │
│   Is SciSpace's Report Writing feature      │
│   production-ready?                         │
│                                             │
│   → We built a hallucination evaluator      │
│     that answers this with evidence.        │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Slide 2: How SciSpace Generates a Report

```
  User Query
      │
      ▼
  ┌──────────────────┐
  │  LLM generates   │
  │  search queries   │──→  SciSpace, Google Scholar, PubMed
  └──────────────────┘
      │
      ▼
  ┌──────────────────┐
  │  Papers retrieved │
  │  & insights       │──→  Intermediary insights report
  │  extracted        │
  └──────────────────┘
      │
      ▼
  ┌──────────────────┐
  │  LLM writes      │
  │  final report     │──→  Report with citations [1]-[30]
  │  with citations   │
  └──────────────────┘
```

The LLM touches the data at **three points**. Each is a hallucination risk.

---

## Slide 3: Three Hallucination Surfaces

```
  Surface 1              Surface 2              Surface 3
  ─────────              ─────────              ─────────
  QUERY                  DIRECTION              FACTS
  HALLUCINATION          FAITHFULNESS           GROUNDING

  Did the search         Did the results        Are the report's
  queries match          stay on course?        claims backed by
  user intent?                                  their cited sources?

  Checked against:       Checked against:       Checked against:
  USER QUERY             USER QUERY             CITED PAPERS
```

Each surface catches something the other two cannot.

---

## Slide 4: Stage 1 — Query Hallucination

**Input:** User query + search queries log

**What we check:**
- LLM extracts user's atomic intents
- Checks if search queries across all channels cover each intent
- Accounts for different query formats per channel:

```
  SciSpace Semantic  →  Natural language (searches abstracts)
  SciSpace Full Text →  Keywords (string match over full PDFs)
  Google Scholar     →  Boolean syntax
  PubMed             →  MeSH medical terms
```

**Metric: Intent Coverage**
> intents covered by ≥1 search query ÷ total intents

---

## Slide 5: Stage 2 — Directional Faithfulness

**Input:** User query + intermediary report

**What we check:**
- Are all user-requested dimensions substantively present?
- Did the report drift into unrelated topics?

```
  User asked:                    Report covers:
  ┌─────────────────┐           ┌─────────────────┐
  │ adherence       │ ────────► │ ✓ adherence     │
  │ accuracy        │ ────────► │ ✓ accuracy      │
  │ long-term       │ ────────► │ ✓ long-term     │
  │ outcomes        │           │ ✗ market trends │ ◄── drift
  └─────────────────┘           └─────────────────┘
```

**Metric: Directional Alignment**
> intents addressed ÷ total intents (penalised if drift detected)

---

## Slide 6: Stage 3 — Claim-Level Fact-Checking

**Input:** Final report (with citations and reference links)

**What we do:**
1. Split report into **atomic factual claims**
2. For each claim, **visit the cited paper** via DOI/URL
3. LLM judge classifies:

```
  ┌─────────────┬─────────────────────────────────────────┐
  │ Supported   │ Source directly says this                │
  │ Unsupported │ Source doesn't say this                  │
  │ Contradicted│ Source says the opposite                 │
  │ Overstated  │ Source says something weaker/more guarded│
  └─────────────┴─────────────────────────────────────────┘
```

**Metric: Grounding Rate**
> supported claims ÷ total verifiable claims

---

## Slide 7: Why "Overstated" Matters

The most common hallucination in research reports is not fabrication — it's **exaggeration**.

```
  Paper says:                    Report writes:
  ──────────                     ─────────────
  "some evidence suggests..."    "research proves..."
  "limited and inconsistent"     "consistently effective"
  "WMD −0.17%"                   "reduced HbA1c by 0.35%"
```

On a research platform, overstating evidence **destroys trust**. It deserves its own label.

---

## Slide 8: How the Evaluator Works

```
  ┌──────────────────────────────────────────────────┐
  │                                                  │
  │   Folder with SciSpace run files                 │
  │   (user query, search log, insights, report)     │
  │                                                  │
  └──────────────────┬───────────────────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────────────────┐
  │  Step 0: LLM classifies & cleans input files     │
  │  (extracts queries from messy log, identifies    │
  │   which file is which)                           │
  └──────────────────┬───────────────────────────────┘
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
     ┌─────────┐ ┌────────┐ ┌──────────┐
     │ Stage 1 │ │Stage 2 │ │ Stage 3  │
     │ Query   │ │Directn │ │ Claims   │
     │ Hallu.  │ │Faithful│ │ Grounding│
     └────┬────┘ └───┬────┘ └────┬─────┘
          │          │           │
          └──────────┼───────────┘
                     ▼
  ┌──────────────────────────────────────────────────┐
  │  Scorecard with evidence                         │
  └──────────────────────────────────────────────────┘
```

- Every eval step uses **LLM-as-judge** with external prompt files
- A PM can edit eval prompts without touching code
- Judge LLM is configurable

---

## Slide 9: The Scorecard (with Evidence)

Not just numbers — **evidence for every failure**.

```
  Stage 3: Claim-Level Fact-Checking
    Grounding Rate .............. 82%     (54/66 supported)

    ✗ CONTRADICTED:
      Claim: "CGM reduced HbA1c by 0.35%"  [6]
      Source says: "WMD −0.17%"
      → Report doubles the effect size.

    ✗ OVERSTATED:
      Claim: "Research proves wearable devices improve
              cardiovascular outcomes" [27]
      Source says: "limited and inconsistent effects"
      → Report presents as proven what the source calls
        inconsistent.
```

Every failure shows: **what the report said**, **what the source said**, and **why it's a problem**.

---

## Slide 10: What This Tells You

Three numbers. Each answers a different question about production readiness.

```
  ┌────────────────────────┬──────────────────────────────┐
  │ Intent Coverage        │ Does the system understand   │
  │                        │ what users are asking?       │
  ├────────────────────────┼──────────────────────────────┤
  │ Directional Alignment  │ Does the system stay on      │
  │                        │ course during research?      │
  ├────────────────────────┼──────────────────────────────┤
  │ Grounding Rate         │ Can you trust what the       │
  │                        │ final report says?           │
  └────────────────────────┴──────────────────────────────┘
```

No arbitrary thresholds. Clear evidence. Run on multiple reports to understand the distribution, then decide.
