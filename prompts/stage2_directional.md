You are evaluating directional faithfulness of an intermediate SciSpace report.

Question: Does the intermediate report stay aligned with the user's intents?

This is not claim-level fact-checking. Check whether the intermediate output is moving in the right direction:
- Does it substantively address each user intent?
- Does it omit important requested dimensions?
- Does it introduce major unrelated topics that would cause drift?

For intent status, use exactly one of:
- addressed
- partially
- not addressed

Return only valid JSON with this exact shape:

```json
{
  "intents": [
    {
      "intent": "intent phrase",
      "status": "addressed",
      "reason": "brief evidence from the intermediate report"
    }
  ],
  "drift": [
    {
      "topic": "unrelated major topic",
      "reason": "why it is unrelated to the user intent"
    }
  ]
}
```

Use an empty drift array if no major drift is present. Do not include commentary.

User intents:

{intents}

Intermediate report:

{report_text}
