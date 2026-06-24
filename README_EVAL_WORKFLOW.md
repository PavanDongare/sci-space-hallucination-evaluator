# SciSpace Evals Workflow

Use this document to quickly copy and paste formatting prompts into a coding agent when evaluating new SciSpace runs. This keeps all inputs and outputs organized under unique run names so nothing is ever overwritten.

## 📁 Workspace Directory Structure

```text
.
├── run_evaluator.py
├── prompts/
└── evaluation_data/
    ├── run_wearables_01/       <-- Formatted inputs & scorecard outputs side-by-side
    └── run_diabetes_02/
```

---

## 📝 The Copy-Paste Prompt for your Coding Agent

When you have a new messy folder, copy the prompt below, fill in the placeholder fields in brackets, and send it to your coding agent:

```markdown
I have a new messy SciSpace run folder that I want to evaluate. 
Please prepare the folder and print the run command for me.

### 1. Inputs
- Messy Source Folder: [INSERT_PATH_TO_MESSY_FOLDER] (e.g., raw_test_input/)
- Described Run Name: [INSERT_RUN_NAME] (e.g., wearables_01)

### 2. Instructions
1. Create the formatted directory: evaluation_data/[INSERT_RUN_NAME]/
2. Identify and copy the raw content into these canonical files in evaluation_data/[INSERT_RUN_NAME]/:
   - user_query.txt
   - search_queries.txt
   - intermediate_report.md
   - final_report.md
3. Extract search queries from the raw log and write them to evaluation_data/[INSERT_RUN_NAME]/search_queries.json in this format:
   [
     { "channel": "SciSpace", "query": "exact query" }
   ]
4. Once completed, print the exact command I should run in my terminal to evaluate this folder:
   python3 run_evaluator.py evaluation_data/[INSERT_RUN_NAME]/ --output evaluation_data/[INSERT_RUN_NAME]/
```
