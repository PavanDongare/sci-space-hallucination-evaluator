You are evaluating query hallucination.

Question: Did the system-generated search queries preserve the user's intents?

Judge by meaning, not by syntax. Different sources require different query styles:
- SciSpace semantic search may be natural language.
- SciSpace full-text search may be a keyword string.
- Google Scholar may use Boolean syntax.
- PubMed may use MeSH terms.

For each intent, decide whether at least one search query substantively covers it.

Return only valid JSON with this exact shape:

```json
{
  "intents": [
    {
      "intent": "intent phrase",
      "covered": true,
      "reason": "which query/channel covers it, or why it is missed"
    }
  ]
}
```

User intents:

{intents}

Search queries:

{search_queries}
