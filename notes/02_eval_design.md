# Eval Design

## Stage 1: Query Hallucination

**Input:** user query + search queries (per channel)

**Question:** Did the generated search queries capture what the user asked for?

**How:**
1. LLM extracts the user's atomic intents from the query.
   - Example: `[wearable health devices, chronic disease management, adherence, accuracy, long-term health outcomes]`
2. For each search query across all channels, the LLM checks which intents it addresses.
   - Each channel has a different format: SciSpace semantic = natural language, SciSpace full-text = keywords (deterministic), Google Scholar = boolean, PubMed = MeSH terms. The judge evaluates meaning, not syntax.

**Metric: Intent Coverage**
> user intents addressed by at least one search query ÷ total user intents

---

## Stage 2: Directional Faithfulness

**Input:** user query + intermediary report (extracted insights)

**Question:** Did the extracted information stay directionally aligned with what the user asked for?

This is not fact-checking (that's Stage 3). This checks whether the system's intermediate output is headed in the right direction. Two ways it can fail:

- **Missing coverage:** a user-requested dimension is absent or barely addressed.
- **Drift:** the report introduces substantial content unrelated to any user intent.

**How:**
1. Using the same atomic intents from Stage 1, the LLM checks whether the intermediary report addresses each intent.
2. The LLM also flags any major topics introduced that are unrelated to any user intent.

**Metric: Directional Alignment**
> user intents substantively addressed ÷ total user intents, penalised if major drift is present

If all intents are addressed and no drift is detected → 100%. If an intent is missing or significant unrelated content is introduced → the score drops accordingly.

---

## Stage 3: Claim-Level Fact-Checking

**Input:** final report (with citations and reference links)

**Question:** Is each factual claim in the final report supported by its cited source?

**How:**
1. LLM splits the final report into atomic factual claims, capturing which citation(s) each references.
2. For each cited paper, visit the DOI/URL from the References section to get the paper's abstract and available content.
3. The LLM judge classifies each claim:

| Label | Meaning |
|---|---|
| **Supported** | The cited source directly says this |
| **Unsupported** | The cited source doesn't say this |
| **Contradicted** | The cited source says the opposite |
| **Overstated** | The source says something in this direction, but weaker or more qualified |

**Metric: Grounding Rate**
> supported claims ÷ total verifiable claims

The breakdown by label is shown in the scorecard as counts for diagnostic clarity. A wrong citation naturally shows up as "unsupported" — so citation accuracy is embedded without a separate metric.

---

## The Scorecard

```
HALLUCINATION EVAL SCORECARD
─────────────────────────────

Stage 1: Query Hallucination
  Intent Coverage ............... 100%    (5/5 intents covered)

Stage 2: Directional Faithfulness
  Directional Alignment ......... 100%    (5/5 intents addressed, no drift)

Stage 3: Claim-Level Fact-Checking
  Grounding Rate ................ 82%     (54/66 claims supported)
    - Supported ................. 54      (82%)
    - Unsupported ............... 6       (9%)
    - Contradicted .............. 1       (2%)
    - Overstated ................ 5       (8%)
```

Three stages. One metric each.

---

## Evaluation Gaps & Rationale

Based on the 5-step SciSpace report-writing architecture, the current evaluator has been expanded to cover Stage 2 Data Extraction (cell-to-abstract checking) and Stage 2 Synthesis Faithfulness (report-to-table checking). However, there are still remaining architectural gaps left out of the current codebase:

### 1. Gap in Step 2: Paper Consolidation
* **Risk:** The system could drop valid papers, duplicate entries, or consolidate metadata incorrectly.
* **LLM-as-a-Judge Needed:** Auditing deduplication and filtering decisions requires semantic reasoning over relevance rather than regex matches. This evaluates the retrieval index rather than report generation.

### 2. Gap in Full-Text Body Grounding
* **Risk:** The evaluator currently checks claims against paper titles and abstracts/summaries stored in the CSV cache. If a claim is supported by a finding in the full paper body but not in the abstract, the evaluator flags it as "Unsupported" or "Overstated".
* **Engineering Needed:** Ingesting full PDFs and chunk-matching claims would increase accuracy but add high latency and cost.

### 3. Gap in Discrete Citation Verification
* **Risk:** When a claim cites multiple references (e.g. `[1, 2, 3]`), the evaluator blends their abstracts together for comparison. If one paper supports the claim but the others do not, the claim is marked supported overall, hiding the faulty citations.
* **Resolution:** Future updates will check claim-citation pairs individually.

### 4. Handling Contradictions and Synthesis Conflicts
* **The Challenge:** When two papers in the consolidated table contradict each other (e.g., Paper A reports positive clinical outcomes, while Paper B reports null findings), how does the evaluator judge the report's synthesis?
* **Synthesis Evaluation Rule:**
  - **Faithful Synthesis:** The report acknowledges the conflict (e.g. *"mixed findings were reported..."*). The synthesis check marks this as **Supported**.
  - **Hallucinated Synthesis:** The report claims consensus (e.g. *"studies consistently prove..."*) while citing both. The synthesis check flags this as **Contradicted** or **Overstated**.
* **Real-World Weighting (Future Metric):** Future pipeline updates should ingest metadata like **H-index**, citation counts, and study design (e.g., RCT vs. observational). This allows the evaluator to audit whether the agent properly prioritized high-strength evidence (high H-index/RCT) when resolving conflicts, rather than weighting all contradictory papers equally.





