Extract the actual search queries from this messy SciSpace search log.

The log may contain status messages, emoji, paper counts, summaries, and unrelated text. Extract only the generated database queries.

Important channel nuance:
- SciSpace semantic search often uses a natural language question because it searches paper abstracts/summaries.
- SciSpace full-text search often uses keyword strings because it searches full PDFs with deterministic text matching.
- Google Scholar often uses Boolean query syntax.
- PubMed often uses MeSH terms and Boolean query syntax.

Return only valid JSON: an array of objects with this exact shape:

```json
[
  {
    "channel": "SciSpace",
    "query": "exact query string"
  }
]
```

Preserve the exact query text, but remove surrounding status text and paper counts. Do not include commentary.

Raw log:

{raw_log}
