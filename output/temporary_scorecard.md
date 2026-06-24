# Cumulative Scorecard (SciSpace Evals Run)

This scorecard summarizes all evaluated dimensions of the SciSpace report-writing run on the `test_input/` folder, explaining exactly how each metric was calculated and what it tells us about the pipeline's reliability.

---

## 📈 Cumulative Metrics Summary

```text
=====================================================================
CUMULATIVE METRICS SUMMARY
=====================================================================
Stage 1: Intent Coverage .............................. 100.0%
Stage 2: Directional Alignment ........................ 100.0%
Stage 2: Data Extraction Accuracy .....................  53.3%
Stage 2: Synthesis Faithfulness .......................  70.0%
Stage 3: Claim Reliability ...........................  24.1%
Stage 3: Cited Grounding Rate .........................  28.4%
=====================================================================
```

---

## 📂 Stage 1: Query Hallucination
* **Metric:** **Intent Coverage: 100.0%** (3/3 intents covered)
* **How it was calculated:** We extracted 3 atomic intents from the user's query and verified that all 3 were successfully targeted by at least one of the generated search queries across our search channels.
* **Interpretation:** Pass. The system understands what the user is asking and generates appropriate search strategies.

---

## 📂 Stage 2: Directional Faithfulness & Data Accuracy
This stage evaluates the correctness of the intermediate data pipeline (the spreadsheet extraction and synthesis).

### 1. Directional Alignment
* **Metric:** **100.0%** (3/3 intents addressed, no informational drift)
* **How it was calculated:** Checks if the intermediate insights report covers all user intents without drifting into major unrelated topics. All requested topics were present.

### 2. Data Extraction Accuracy
* **Metric:** **53.3%** (8/15 criteria cells accurate)
* **How it was calculated:** We verified the top 5 papers in the consolidated CSV table. For each paper, we checked 3 criteria columns (*Study Design*, *Key Findings*, and *Limitations*) directly against the paper's abstract (15 total cells checked). Exactly 8 were supported, while 7 contained hallucinated or exaggerated details.

### 3. Synthesis Faithfulness
* **Metric:** **70.0%** (7/10 report claims faithful)
* **How it was calculated:** We compared the first 10 factual claims in the final report against the consolidated table. The LLM judge found that 7 of these claims faithfully reflected the table data, while 3 claims introduced external context or overstated counts not documented in the table.

---

## 📂 Stage 3: Claim-Level Fact-Checking
This stage evaluates the absolute factual grounding of the final report against the source literature.

### 1. Claim Reliability
* **Metric:** **24.1%** (27/112 non-common claims supported)
* **How it was calculated:** We extracted all 112 factual claims from the final report (excluding common knowledge). When verifying these claims against the cited literature, the LLM judge found that only 27 claims were fully supported by the cited papers, while 85 were either unsupported, overstated, or uncited.

### 2. Cited Grounding Rate
* **Metric:** **28.4%** (27/95 cited claims supported)
* **How it was calculated:** Out of the 112 claims, we excluded the 17 claims that had no citations attached. Of the remaining 95 cited claims, only 27 were fully supported by their referenced papers.

---

## 🔍 Key Presentation Takeaways

* **The Leakage Pipeline:** The system looks excellent at the front-end (Stage 1 & Stage 2 Alignment are 100%), but leaks quality at every step of data processing.
* **Extraction vs. Synthesis Errors:** Having both Stage 2 metrics allows us to pinpoint that 46.7% of the errors are introduced during the spreadsheet extraction phase, and another 30.0% are introduced when merging those cells into the final report.
