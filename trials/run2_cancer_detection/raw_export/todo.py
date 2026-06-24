Planner Code plan:
```python
def main():
    # 1. Search for scholarly literature on AI-based early cancer detection across multiple domains.
    # This covers imaging, genomics, and multimodal approaches as requested.
    search_results = search_scholarly_literature(
        query="AI-based early cancer detection performance imaging genomics multimodal AUC sensitivity specificity",
        source="SciSpace"
    )

    # 2. Extract key metrics (AUC, sensitivity, specificity) and comparative insights 
    # from the search results to ensure data-driven reporting.
    extraction_query = (
        "Extract performance metrics (AUC, sensitivity, specificity) for early cancer detection "
        "using AI in imaging, genomics, and multimodal approaches. Create a comparison of these methods."
    )
    insights = extract_insights_from_search_results(
        questions=[extraction_query],
        return_reply_to_user=False
    )

    # 3. Synthesize the findings into a professional markdown report.
    # write_report handles the structure, citations, and table generation based on the extracted insights.
    report_task = (
        "Create a comprehensive report on AI-based early cancer detection methods. "
        "Compare performance across imaging, genomics, and multimodal approaches. "
        "Include tables for AUC, sensitivity, and specificity. Use the following insights: " + str(insights)
    )
    write_report(
        user_prompt=report_task,
        content_format="markdown"
    )

if __name__ == "__main__":
    main()
```