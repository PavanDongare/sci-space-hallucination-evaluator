Extract the atomic user intents from this research query.

An intent is one distinct topic, dimension, constraint, comparison, population, outcome, or focus area that the generated searches and reports should preserve.

Guidelines:
- Keep each intent short and concrete.
- Do not invent requirements that are not in the query.
- Split compound requests when each part should be checked independently.

Return only valid JSON: an array of objects with this exact shape:

```json
[
  {
    "intent": "short intent phrase"
  }
]
```

User query:

{query}
