# SciSpace Evals Workflow

Use this document to quickly copy and paste formatting prompts into a coding agent when evaluating new SciSpace runs. This keeps all inputs and outputs organized under unique run names so nothing is ever overwritten.

## 📁 Workspace Directory Structure

```text
scispace-evals/
├── inputs/
│   ├── run_wearables_01/       <-- Formatted inputs
│   └── run_diabetes_02/
├── outputs/
│   ├── run_wearables_01/       <-- Evaluator output (scorecard.md, detailed_log.json)
│   └── run_diabetes_02/
├── eval.py
└── prompts/
```

---

## 📝 The Copy-Paste Prompt for your Coding Agent

When you have a new messy folder, copy the prompt below, fill in the placeholder fields in brackets, and send it to your coding agent:

```markdown
I have a new messy SciSpace run folder that I want to evaluate. 
Please prepare the folder and print the run command for me.

### 1. Inputs
- Messy Source Folder: [INSERT_PATH_TO_MESSY_FOLDER] (e.g., test_input/)
- Described Run Name: [INSERT_RUN_NAME] (e.g., wearables_01)

### 2. Instructions
1. Create the formatted directory: inputs/[INSERT_RUN_NAME]/
2. Identify and copy the raw content into these canonical files in inputs/[INSERT_RUN_NAME]/:
   - user_query.txt
   - search_queries.txt
   - intermediate_report.md
   - final_report.md
3. Extract search queries from the raw log and write them to inputs/[INSERT_RUN_NAME]/search_queries.json in this format:
   [
     { "channel": "SciSpace", "query": "exact query" }
   ]
4. Once completed, print the exact command I should run in my terminal to evaluate this folder:
   python eval.py inputs/[INSERT_RUN_NAME]/ --output outputs/[INSERT_RUN_NAME]/
```
