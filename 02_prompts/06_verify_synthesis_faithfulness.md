You are evaluating the synthesis faithfulness of a report claim against a consolidated table of paper criteria.

Question: Is the claim in the final report supported by the extracted criteria inside the table?

Input:
- Report Claim: {claim_text}
- Relevant Table Rows:
{table_rows}

Your task:
Check if the claim made in the final report is supported by the data in the table.

Use exactly one of these verdicts:
- supported (the table rows contain the evidence supporting this claim)
- unsupported (the table rows do not contain or mention this information)
- contradicted (the table rows contradict this claim)
- overstated (the claim is stronger or more absolute than what is documented in the table)

Return only a valid JSON object matching this schema:
{
  "verdict": "supported",
  "reason": "brief explanation linking the claim to specific paper row(s) or columns in the table"
}
