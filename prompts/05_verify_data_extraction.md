You are verifying the accuracy of a data extraction cell from a consolidated paper table.

Question: Is the extracted cell value supported by the paper abstract?

Input:
- Criteria Name: {criteria_name}
- Cell Value: {cell_value}
- Paper Title: {paper_title}
- Paper Abstract: {paper_abstract}

Your task:
Judge whether the cell value is supported, unsupported, contradicted, or overstated based ONLY on the provided paper title and abstract.

Use exactly one of these verdicts:
- supported (the abstract fully supports the cell value)
- unsupported (the abstract does not mention or support this information)
- contradicted (the abstract directly contradicts this information)
- overstated (the cell value is stronger, more absolute, or exaggerates what the abstract says)

Return only a valid JSON object matching this schema:
{
  "verdict": "supported",
  "reason": "brief explanation citing the evidence from the abstract"
}
