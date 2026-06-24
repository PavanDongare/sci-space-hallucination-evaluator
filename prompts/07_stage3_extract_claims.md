Split this final report into atomic factual claims for citation checking.

Include only factual assertions that can be checked against cited sources. Skip:
- headings
- table-of-contents items
- transitions
- purely subjective statements
- generic methodology narration
- broad common-knowledge claims that do not need citation

Do include niche-specific factual claims even when they have no citation. These are important because uncited factual claims are a hallucination risk. Use an empty `citation_ids` array for them and set `is_common_knowledge` to false.

Each claim should be one atomic fact. Preserve the citation numbers attached to that claim.

Return only valid JSON: an array of objects with this exact shape:

```json
[
  {
    "claim_text": "exact or lightly normalized factual assertion",
    "citation_ids": [1, 5],
    "is_common_knowledge": false
  }
]
```

If a factual claim has no citation, use an empty citation_ids array. Do not include commentary.

Final report:

{report_text}
