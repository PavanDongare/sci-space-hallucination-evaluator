You are judging whether one report claim is grounded in its cited source.

Judge only from the provided source text. Do not use outside knowledge.

Labels:
- supported: the source directly states or clearly implies the claim.
- unsupported: the source does not say the claim.
- contradicted: the source says the opposite of the claim.
- overstated: the source points in the same direction, but the report is stronger, broader, more certain, or less qualified than the source.

Return only valid JSON with this exact shape:

```json
{
  "verdict": "supported",
  "reason": "one sentence explaining the verdict",
  "source_says": "brief quote or paraphrase of what the source says"
}
```

Claim:

{claim_text}

Citation IDs:

{citation_ids}

Source text:

{paper_content}
