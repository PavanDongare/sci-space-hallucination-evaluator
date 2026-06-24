You are classifying files from one SciSpace report-writing run.

You will receive file names and short previews. Pick the files needed by the evaluator.

Roles:
- user_query: the original user request. Usually short plain text.
- search_queries: the log of generated searches across databases. It often includes "Searched SciSpace", "Searched Google Scholar", paper counts, and status text.
- intermediate_report: an insights, extraction, or summary markdown produced before the final report.
- final_report: the full report. Usually long markdown with inline citations like [1] and a References section.

Ignore CSVs, scripts, todo files, assignment docs, and other files that are not needed.

Return only valid JSON with this exact shape:

```json
{
  "user_query": "relative/path/or/null",
  "search_queries": "relative/path/or/null",
  "intermediate_report": "relative/path/or/null",
  "final_report": "relative/path/or/null"
}
```

Use null when a role is not present. Do not include commentary.

File previews:

{file_previews}
