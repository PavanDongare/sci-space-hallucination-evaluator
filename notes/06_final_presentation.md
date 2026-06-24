# Presentation: SciSpace Hallucination Evals

---

## Slide 1: The Hook

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   "Just feed the report to a stronger LLM and ask   │
│    whether it hallucinated."                        │
│                                                     │
│   Sounds simple. It is the wrong first answer.      │
│                                                     │
│   The LLM can sound right and still be wrong.       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

This is the first instinct.

---

## Slide 2: Then I Thought, Citations Fix It

```
Report looks correct
   │
   ▼
Citations look correct too
   │
   ▼
But the claim still may not be grounded
```

I thought: if the report sounds right, citations should catch the error.

That helps, but only if the cited source really supports the claim. A strong LLM can still sound confident and still overstate, understate, or invent support.

That is why the bottom layer exists.

---

## Slide 3: Then I Thought, Maybe The Document Is Wrong

```
The citation is real
   │
   ▼
The source text is real
   │
   ▼
But the source may be irrelevant to the user's intent
```

I thought: okay, the claim is cited. But what if the cited paper is not actually the right evidence for what the user asked?

That is why we check directional faithfulness. The report can be factually grounded and still point at the wrong part of the problem.

---

## Slide 4: Then I Thought, Maybe We Queried The Wrong Thing

```
Wrong query
   │
   ▼
Wrong retrieval path
   │
   ▼
Wrong final report
```

I thought: even if the source is right, what if the search query itself was wrong from the beginning?

That is the first failure surface. If the system asks the databases the wrong thing, everything downstream can still look polished and still miss the user.

---

## Slide 5: Why The Layers Exist

```
Top failure  ── Query Hallucination (Asking correct question)
Middle failure ─ Directional Drift & Data Accuracy (Getting correct data)
Bottom failure ─ Claim Grounding (Being factually correct)
```

The ordering is deliberate and matches the research workflow:

- Stage 1 checks if the system searched the right thing (Query).
- Stage 2 checks if we gathered accurate, relevant data and synthesized it faithfully (Data).
- Stage 3 checks if the final report is grounded in the literature (Factuality).

That is why the layers run top to bottom. If the top layer fails, the system is already not ready, even if the bottom looks good.

---

## Slide 7: Stage 1 - Query Hallucination

**Question:** Did the system generate search queries that match the user intent?

**Input:** user query + search queries

**Why this matters:** if the search step misses intent, the entire retrieval path starts wrong.

**Channel nuance:**

```
SciSpace semantic   -> natural language over abstracts
SciSpace full text   -> keyword search over full PDFs
Google Scholar      -> Boolean syntax
PubMed              -> MeSH / Boolean syntax
```

The judge scores meaning, not syntax. A keyword string and a question can both be correct if they target the same intent.

**Metric: Intent Coverage Rate (IC)**
* **Numerator:** Number of user intents targeted by at least one generated search query.
* **Denominator:** Total number of unique atomic user intents extracted from the query.
* **Plain-English Definition:** What percentage of the user's request did we actually search for?

---

## Slide 8: Stage 2 Evaluation Matrix (Mid-Pipeline Assessment)

**Question:** Are we getting the correct data and synthesizing it on-track?

We break Stage 2 down into three distinct matrices to locate exactly where data corruption or drift occurs in the middle pipeline:

1. **Directional Alignment Matrix:**
   * *Target:* Semantic intent preservation in the intermediate report.
   * *How it is judged:* The LLM judge compares the intermediate report text against the extracted atomic intents. Each intent is scored as:
     - **Addressed (1.0):** The topic is fully and accurately discussed.
     - **Partially (0.5):** The topic is mentioned but lacks depth.
     - **Missing (0.0):** The topic is omitted.
   * *Drift Penalty:* Any major topic introduced that is unrelated to the user's intents is flagged as "drift" (penalizing the score by 0.2 per drift topic).
   * *Calculation Rule (Directional Alignment Rate - DA):*
     - **Numerator:** Sum of intent scores minus Drift Penalties.
     - **Denominator:** Total count of extracted user intents.
   * *Rationale:* Prevents the model from writing a highly grounded report that completely misses the user's primary medical/scientific questions.

2. **Data Extraction Accuracy Matrix:**
   * *Target:* Veracity of database values before writing.
   * *How it is judged:* For each paper, we check the criteria cells in the spreadsheet (e.g. Study Design, Key Findings, Limitations) against the paper's original abstract. Each cell is labeled as supported, unsupported, contradicted, or overstated.
   * *Calculation Rule (Data Extraction Accuracy - EA):*
     - **Numerator:** Number of spreadsheet cells verified as factually supported by their original paper abstracts.
     - **Denominator:** Total number of spreadsheet cells scored (Number of Papers checked x Number of Columns checked).
   * *Rationale:* Catching extraction errors early. If the database is corrupt, the final report cannot be correct.

3. **Synthesis Faithfulness Matrix:**
   * *Target:* Writing fidelity to the extracted data.
   * *How it is judged:* Compares the claims in the final report to the rows of the spreadsheet table. The LLM verifies if the writer fabricated new facts, inflated counts, or added undocumented clinical benefits not present in the table.
   * *Calculation Rule (Synthesis Faithfulness - SF):*
     - **Numerator:** Number of final report claims verified as faithful to the spreadsheet table.
     - **Denominator:** Total number of final report claims checked against the spreadsheet table.
   * *Rationale:* Pinpoints whether hallucinations are introduced during writing (Synthesis) or reading (Extraction).

---

## Slide 9: Stage 3 Evaluation Matrix (Factual Grounding)

**Question:** Is every factual statement in the final report fully supported by the cited literature?

This is our primary grounding gate. The evaluator extracts all non-common-knowledge claims and classifies them against their cited paper abstracts using a natural language inference (NLI) judge:

| Verdict Label | Operational Definition | Scoring Status |
| :--- | :--- | :---: |
| **Supported** | The claim is fully and directly supported by the text in the cited source. | Pass |
| **Unsupported** | The source text does not mention or contain any evidence for the claim. | Fail |
| **Contradicted** | The source text explicitly states the opposite of the claim. | Fail |
| **Overstated** | The source text supports the general direction, but the report exaggerates the findings (e.g., claiming a "20% reduction in hospitalizations" when the abstract reports no specific percentage). | Fail |
| **Uncited** | A specific factual assertion (e.g., stating clinical trial sample sizes or dates) is made with no citation attached. | Fail |
| **Not Verifiable** | No cited source could be matched or retrieved for this citation ID. | Fail |

---

### **Calculations Derived From This Matrix:**

1. **Claim Reliability Rate (CR):**
   * **Numerator:** Count of factual claims labeled as **Supported**.
   * **Denominator:** Total factual claims extracted from the report (Supported + Unsupported + Contradicted + Overstated + Uncited + Not Verifiable).
   * **Plain-English Definition:** The absolute truth rate of the report. What percentage of all statements written are actually true?

2. **Cited Grounding Rate (CGR):**
   * **Numerator:** Count of factual claims labeled as **Supported**.
   * **Denominator:** Total scored claims minus **Uncited** claims (only claims that have a citation).
   * **Plain-English Definition:** When the writer did cite a source, how often was it the correct source? (Isolates citation accuracy from missing citations).

---

## Slide 10: Static Verification vs. Semantic Judge Matrix

Not all verification steps require expensive LLM calls. We split the workload to ensure high speed and reliability:

### **Static Verification (Deterministically Scored)**
* **Folder Contract Compliance:** Verifies files (`user_query.txt`, `search_queries.txt`, `intermediate_report.md`, `final_report.md`) exist.
* **Citation Integrity:** Verifies that inline citations (e.g. `[1]`, `[2]`) correspond to numbered entries in the References section.
* **URL / DOI Extraction:** Parses DOIs and HTTPS links using regex to confirm formatting.
* **Retrieval Checks:** Verifies that cited DOIs are resolvable via local database caches or web APIs (Crossref/Semantic Scholar).

### **Semantic Judges (LLM-as-a-Judge)**
* **Intent Extraction:** Formulates discrete goals from messy user queries.
* **Coverage Matching:** Fuzzy semantic classification of database queries against intents.
* **Directional Drift Analysis:** Scanning intermediate text for topical relevance.
* **NLI Grounding (Cell vs. Abstract & Claim vs. Abstract):** Natural Language Inference checks to categorize claims into Supported, Unsupported, Contradicted, or Overstated.

---

## Slide 11: The Input Contract (Directory Preparation)

For the evaluator to execute cleanly, inputs are pre-processed by a preparation workflow.

```text
scispace-evals/
├── test_input/
│   ├── user_query.txt          <-- Raw user query string
│   ├── search_queries.txt      <-- Raw log of channel searches
│   ├── search_queries.json     <-- Optional: Pre-cleaned channel/query pairs
│   ├── intermediate_report.md  <-- Insights report
│   ├── wearable_health_devices_chronic_disease_report.md <-- Final report with references
│   └── scispace_wearable_health_devices.csv  <-- Local papers database
```

This preparation step runs before evaluation, ensuring the runner receives standardized files, preventing parsing failures during evaluation.

---

## Slide 12: Technical Metrics Dictionary & Calculations

To establish a clear engineering standard, every metric in the SciSpace evaluator is calculated using plain-English ratios. Below is the documentation of definitions, inputs, calculations, and the specific failure modes they detect:

---

### **1. Intent Coverage Rate (IC) — Stage 1 (Query Validation)**
* **Calculation:** 
  `IC = (Number of Intents Covered by 1 or more Queries) / Total Extracted Intents`
* **Numerator:** Unique user intents semantic-matched to at least one generated search query.
* **Denominator:** Total unique atomic user intents extracted from the user's query.
* **Plain-English Definition:** The percentage of user requirements targeted by the system's generated search queries.
* **Failure Mode Prevented:** **Query Omission.** If the user asks about "sensor accuracy in clinical environments" but the query generator only searches for "wearable health device outcomes," this metric flags the gap before papers are retrieved.

---

### **2. Directional Alignment Rate (DA) — Stage 2 (Insights Validation)**
* **Calculation:** 
  `DA = (Sum of Intent Scores - Drift Penalties) / Total Extracted Intents`
* **Numerator:** Sum of intent scores (1.0 if fully discussed, 0.5 if partially addressed, 0.0 if ignored) minus Drift Penalties (0.2 deduction per major topic introduced in the report that does not map to any user intent).
* **Denominator:** Total unique atomic user intents extracted from the user's query.
* **Plain-English Definition:** The degree to which the intermediate insights report stays on-topic and covers the user's goals.
* **Failure Mode Prevented:** **Informational Drift & Topic Deletion.** Prevents the writing model from ignoring difficult user requirements or writing sections about unrelated research fields.

---

### **3. Data Extraction Accuracy (EA) — Stage 2 (Spreadsheet Validation)**
* **Calculation:** 
  `EA = Supported Cells in Spreadsheet / Total Cells Scored`
* **Numerator:** Count of spreadsheet cell values that are factually true and supported by the original paper abstracts.
* **Denominator:** Total cell evaluations performed (Calculated as: Number of Papers checked x Number of Criteria Columns checked, e.g. 5 papers checked across 3 columns = 15 cells).
* **Plain-English Definition:** The factual precision of data loaded into database cells from retrieved papers.
* **Failure Mode Prevented:** **Spreadsheet Hallucination.** Prevents the model from populating tables with fake sample sizes, incorrect follow-up times, or exaggerated outcomes.

---

### **4. Synthesis Faithfulness (SF) — Stage 2 (Synthesis Validation)**
* **Calculation:** 
  `SF = Report Claims Faithful to Table / Total Claims Checked Against Table`
* **Numerator:** Report statements that are strictly traceable to the spreadsheet table, without additions or fabrication.
* **Denominator:** The total number of claims in the final report checked against the table.
* **Plain-English Definition:** The writer's fidelity to the extracted structured database, verifying it does not add external claims.
* **Failure Mode Prevented:** **Context Leakage & Authoritativeness Inflation.** Catches cases where the writer claims consensus over a large study sample (e.g. "synthesized from 93 studies") when the underlying table only contains 10 rows.

---

### **5. Claim Reliability Rate (CR) — Stage 3 (Report Factuality)**
* **Calculation:** 
  `CR = Supported Claims / Total Extracted Claims`
* **Numerator:** Atomic factual assertions in the final report that are fully supported by their cited paper abstracts.
* **Denominator:** The total number of factual assertions made in the report, excluding common knowledge.
* **Plain-English Definition:** The overall factual correctness and grounding of the final report relative to the source literature.
* **Failure Mode Prevented:** **Factual Hallucination.** This is the primary user safety gate, preventing the publication of reports with untrue or overstated facts.

---

### **6. Cited Grounding Rate (CGR) — Stage 3 (Attribution Quality)**
* **Calculation:** 
  `CGR = Supported Claims / (Total Scored Claims - Uncited Claims)`
* **Numerator:** Atomic factual assertions in the final report that are fully supported by their cited paper abstracts.
* **Denominator:** Total scored claims minus any claims that had no bibliography link attached.
* **Plain-English Definition:** The accuracy of the bibliography links, measuring whether citations point to the correct supporting evidence.
* **Failure Mode Prevented:** **Attribution Mismatch.** Isolates cases where the report's facts are correct, but the inline citations point to irrelevant papers, which is a major academic/clinical trust failure.

---

## Slide 13: Trial Run 1 Results (Wearables for Chronic Disease)

This scorecard evaluates the Wearable Health Devices run against the cached literature database.

### **1. User Query**
```text
Create a report on wearable health devices for chronic disease management, focusing on adherence, accuracy, and long-term health outcomes.
```

### **2. Generated Search Queries (Intent Coverage)**
* **SciSpace (Semantic):** *"What are the effects of wearable health devices on chronic disease management, patient adherence, measurement accuracy, and long-term health outcomes?"*
* **SciSpace (Full Text):** *"wearable health devices chronic disease management adherence accuracy long-term outcomes"*
* **Google Scholar (Boolean):** `(wearable OR "wearable device" OR "wearable technology" OR smartwatch OR fitness tracker) AND ("chronic disease" OR "chronic illness" OR diabetes OR hypertension OR "heart disease" OR "cardiovascular disease") AND (adherence OR compliance OR "patient compliance") AND (accuracy OR validity OR reliability) AND ("health outcomes" OR "clinical outcomes" OR "long-term outcomes")`
* **PubMed (MeSH/Boolean):** `(wearable devices[MeSH] OR wearable technology OR smartwatch OR fitness tracker OR wearable sensor) AND (chronic disease[MeSH] OR diabetes mellitus[MeSH] OR hypertension[MeSH] OR cardiovascular diseases[MeSH] OR chronic illness) AND (medication adherence[MeSH] OR patient compliance[MeSH] OR adherence) AND (accuracy OR validity OR reliability) AND (treatment outcome[MeSH] OR health outcomes OR long-term outcomes OR clinical outcomes)`
* **Intent Coverage Score:** **100.0%** (3/3 atomic intents covered by search queries).

### **3. Data Synthesis & Data Accuracy (Mid-Pipeline)**
* **Directional Alignment:** **100.0%** (3/3 intents discussed in the intermediate insights report without topic drift).
* **Data Extraction Accuracy:** **53.3%** (8/15 spreadsheet cells verified as factually true to paper abstracts).
* **Synthesis Faithfulness:** **70.0%** (7/10 report claims verified as faithful to the spreadsheet table).

### **4. Citation Groundedness (Factual Grounding)**
* **Claim Reliability Rate (CR):** **24.1%** (27/112 factual claims supported by paper abstracts).
* **Cited Grounding Rate (CGR):** **28.4%** (27/95 cited claims supported; 17 claims were entirely uncited).
* **Important Caveat (Abstract-Based Evaluation):**
  > [!NOTE]
  > Because of runtime and caching restrictions, the evaluator ran verification checks strictly against **locally available paper abstracts** rather than full-text PDF documents. Because abstracts are brief summaries and omit detailed cohort descriptions or secondary metrics, many correct claims inside the report body are flagged as "unsupported." The actual rate of hallucinations might be significantly better (i.e., a higher grounding rate) if run against the complete full-text PDF data.

---

## Slide 13b: Trial Run 2 Results (AI-Based Early Cancer Detection)

This scorecard evaluates the Early Cancer Detection run against the cached literature database.

### **1. User Query**
```text
Create a report on AI-based early cancer detection methods, comparing performance across imaging, genomics, and multimodal approaches using metrics like AUC, sensitivity, and specificity.
```

### **2. Generated Search Queries (Intent Coverage)**
* **SciSpace (Semantic):** *"What are the AI-based approaches for early cancer detection using imaging and genomics with performance metrics like AUC, sensitivity, and specificity in multimodal systems?"*
* **SciSpace (Full Text):** *"AI early cancer detection AUC sensitivity specificity imaging genomics multimodal deep learning machine learning performance comparison"*
* **Google Scholar (Boolean):** `(artificial intelligence OR AI OR "deep learning" OR "machine learning") AND ("early cancer detection" OR "cancer screening") AND (AUC OR sensitivity OR specificity OR "performance metrics") AND (imaging OR genomics OR multimodal OR "multi-modal")`
* **PubMed (MeSH/Boolean):** `(artificial intelligence[Title/Abstract] OR deep learning[Title/Abstract] OR machine learning[Title/Abstract]) AND (early detection of cancer[MeSH] OR cancer screening[Title/Abstract] OR early cancer detection[Title/Abstract]) AND (AUC[Title/Abstract] OR sensitivity[Title/Abstract] OR specificity[Title/Abstract]) AND (imaging[Title/Abstract] OR genomics[Title/Abstract] OR multimodal[Title/Abstract])`
* **arXiv (API syntax):** `all:artificial+intelligence+AND+all:cancer+detection+AND+all:AUC+AND+(all:imaging+OR+all:genomics+OR+all:multimodal)`
* **Intent Coverage Score:** **40.0%** (2/5 intents covered).
  * *Analysis:* The system generated queries covering "AI early cancer detection" and "performance metrics" but failed to generate distinct comparative queries contrasting the individual modalities (imaging, genomics, and multimodal) against each other.

### **3. Data Synthesis & Data Accuracy (Mid-Pipeline)**
* **Directional Alignment:** **100.0%** (5/5 intents addressed in report).
* **Data Extraction Accuracy:** **Skipped** (No structured database spreadsheet table was output by the system during this run).
* **Synthesis Faithfulness:** **Skipped** (No database table was available to verify writing fidelity against).

### **4. Citation Groundedness (Factual Grounding)**
* **Claim Reliability Rate (CR):** **32.7%** (33/101 factual claims supported by paper abstracts).
* **Cited Grounding Rate (CGR):** **66.0%** (33/50 cited claims supported; 51 claims were entirely uncited).
* **Important Caveat (Abstract-Based Evaluation):**
  > [!NOTE]
  > Because of runtime and caching restrictions, verification was conducted strictly using **locally available paper abstracts** rather than full-text PDF documents. As a result, correct claims containing specific statistics or background context (which are supported in the full PDF body but omitted in the brief abstract) were flagged as "unsupported." The actual rate of hallucinations might be significantly better (i.e., a higher grounding rate) if run against the complete full-text PDF data.

---

## Slide 13c: The Cascading Quality Leakage Comparison

Contrasting both runs highlights the compounding nature of pipeline quality degradation:

```text
[Stage 1: Intent Coverage] -------> Wearables: 100.0%  |  Cancer: 40.0%
        │
        ▼
[Stage 2: Directional Alignment] -> Wearables: 100.0%  |  Cancer: 100.0%
        │
        ▼
[Stage 2: Data Extraction] -------> Wearables: 53.3%   |  Cancer: Skipped (Schema mismatch)
        │
        ▼
[Stage 2: Synthesis Faithfulness] -> Wearables: 70.0%   |  Cancer: Skipped (Schema mismatch)
        │
        ▼
[Stage 3: Claim Reliability] ------> Wearables: 24.1%   |  Cancer: 32.7%
```

### **The Mechanics of Compounding Degradation:**
* **Run 1 (Wearables):** Although search queries and directions were 100% aligned, data corrupted during extraction (53.3%) and synthesis (70.0%), leading to a low final grounding score of 24.1% (37.3% expected joint data integrity).
* **Run 2 (Cancer):** The system missed generating comparative queries (40.0% intent coverage) but wrote a well-aligned report (100% directional alignment). Without a database extraction step to corrupt the data, the grounding rate reached 32.7% (CGR 66.0%), outperforming Run 1 despite the poor search coverage.

---

## Slide 13d: Concrete Case Studies (Rigor and Evidence)

Here is the exact ground truth evidence and verdicts generated by the evaluator on both datasets:

### **Run 1 (Wearables) Case Studies**
* **Extraction Mismatch (Spreadsheet vs. Paper Abstract):**
  - *Criteria:* Limitations and Gaps
  - *Extracted Cell Value:* *"specifically using wearable devices for COPD to enhance telehealth outcomes..."*
  - *Actual Abstract Text:* *"Interventions are growing and their effectiveness to monitor telehealth outcomes has not been systematically reviewed."* (COPD is never mentioned in the abstract).
  - *Verdict:* **Unsupported / Hallucinated**.
* **Synthesis Mismatch (Report Claim vs. Spreadsheet Rows):**
  - *Report Claim:* *"A scoping review of 79 intervention studies found that activity trackers were the most commonly studied device type..."*
  - *Spreadsheet Table:* The table contains only 10 rows. The scoping review in the table (Paper [9]) lists a review of 7 meta-analyses and 20 RCTs, not 79 studies.
  - *Verdict:* **Unsupported**. The model hallucinated external clinical trial figures to sound authoritative.

### **Run 2 (Cancer) Case Studies**
* **Rounding / Precision Mismatch (Claim vs. Cited Abstract):**
  - *Report Claim:* *"Multi-cancer detection using blood cfDNA/methylation (MCED) with ensemble ML achieved AUC up to 0.993."* (Citing Paper [10]).
  - *Cited Abstract Text:* *"...area under the curve (AUC) in included studies were 0.9929."*
  - *Verdict:* **Unsupported / Overstated** (strict rounding check by the evaluator judge).
* **Topical Extrapolation (Claim vs. Cited Abstract):**
  - *Report Claim:* *"False positives remain a persistent challenge in imaging-based AI, leading to unnecessary biopsies."* (Citing Papers [2], [6]).
  - *Cited Abstract Text:* Paper [2] reports *"specificity remained variable"*; Paper [6] discusses sensitivity at fixed specificity levels. Neither discusses biopsy consequences or calls it a "persistent challenge."
  - *Verdict:* **Unsupported** (strict semantic grounding check due to abstract brevity).

---

## Slide 14: Model Choice & Cost-vs-Accuracy Tradeoffs

For developmental testing, smaller models like `deepseek-v4-flash` or `gemini-2.5-flash` are highly effective:
* **Iteration Velocity:** They are cheap, fast, and let us quickly validate the evaluator's logic and pipeline parsing.
* **Production Decision Warning:** For final assessments that inform product shipping decisions, **we must use stronger frontier models (e.g. Claude 3.5 Sonnet, GPT-4o)**.
* **Reasoning:** Flash models are prone to making errors on subtle semantic grounding checks. The accuracy of the LLM judge directly limits the validity of our readiness scores; saving on the token bill is not worth shipping a hallucinated product.

---

## Slide 15: Remaining Evaluation Gaps

While we have implemented Stage 2 Data Extraction Accuracy and Synthesis Faithfulness checking, some architectural gaps remain outside the current evaluator scope:

1. **Step 2 (Paper Consolidation) Audit:**
   * *Risk:* The search database can drop relevant papers, duplicate studies, or fabricate metadata.
   * *LLM-as-a-Judge Needed:* Auditing deduplication and relevance filtering requires semantic reasoning, which evaluates the search index itself rather than report writing.
2. **Full-Text PDF Grounding:**
   * *Risk:* Currently we check claims against paper titles and abstracts. Valid claims supported inside a paper body but not in the abstract might be false-flagged as unsupported.
   * *Engineering Needed:* Building full-text ingestion, PDF OCR, and text-chunk retrieval would prevent these false-positives but add significant latency.
3. **Discrete Citation-Pair Checking:**
   * *Risk:* If a claim cites `[1, 2, 3]`, we blend their abstracts to test grounding. If `[1]` supports it but `[2, 3]` are completely irrelevant, the claim is still marked "Supported", masking bad citations.
   * *Engineering Needed:* Expanding the claim definition to verify each citation ID individually.

---

## Slide 15b: Synthesis Conflicts & H-Index Prioritization

A critical challenge in report synthesis is how the agent resolves contradictions between papers (e.g., Paper A reports positive findings, Paper B reports null findings).

* **Auditing Conflicts:** 
  - **Faithful Synthesis:** The report acknowledges the conflict (e.g. *"mixed findings were reported..."*). 
  - **Hallucinated Synthesis:** The report claims consensus (e.g. *"studies consistently prove..."*) while citing both. Our synthesis check flags this as **Contradicted** or **Overstated**.
* **H-Index Weighting (Future Feature):** 
  In the real world, researchers prioritize papers by evidence quality. Future iterations of the evaluator should ingest paper metadata (H-index, citation counts, RCT vs. observational) to check if the agent correctly prioritized high-strength evidence when resolving conflicts.

---

## Slide 16: Production Readiness Threshold Matrix

To safely ship this product to clinical or academic users, we establish a safety threshold comparison matrix:

| Metric | Target Safety Threshold | Trial Run 1 (Wearables) | Trial Run 2 (Cancer) | Delta to Ship (Run 1 / Run 2) | Technical Action Plan |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Intent Coverage** | >= 98.0% | 100.0% | 40.0% | +0.0% / **-58.0%** | Run 2 query generator failed to create comparative search queries. Improve query templates. |
| **Directional Alignment** | >= 98.0% | 100.0% | 100.0% | +0.0% / +0.0% | *Passed.* Maintain outline and semantic alignment checks. |
| **Data Extraction Accuracy** | >= 95.0% | 53.3% | Skipped | **-41.7%** / N/A | Enforce strict schemas and context limits in Step 4. |
| **Synthesis Faithfulness** | >= 95.0% | 70.0% | Skipped | **-25.0%** / N/A | Constrain Step 5 writing prompts to only reference spreadsheet values. |
| **Claim Reliability** | >= 90.0% | 24.1% | 32.7% | **-65.9%** / **-57.3%** | Inject verification step to remove ungrounded assertions. |

### **FINAL VERDICT: NOT PRODUCTION-READY**
Neither pipeline is ready for public release. A user relying on these reports is highly likely to make clinical or academic decisions based on fabricated statistics and false citations.

### **Engineering Recommendations to Achieve Readiness:**
1. **Spreadsheet Extraction Constraints:** Enforce strict grounding prompts in Step 4 to ensure table cell values never extrapolate beyond the source PDF text.
2. **Synthesis Grounding Enforcement:** Constrain the final writing model (Step 5) to write claims that are strictly traceable back to the columns of the consolidated table, preventing general knowledge leakage.
3. **Bibliography Validation:** Add a verification pass that rejects any citation where the parsed claim does not map to a confirmed statistical finding in the paper.
