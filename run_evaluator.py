#!/usr/bin/env python3
"""SciSpace hallucination evaluator CLI."""

from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_API_BASE = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o"
DEFAULT_AGY_MODEL = "Gemini 3.5 Flash (Low)"
MAX_FILE_BYTES = 500_000
PREVIEW_CHARS = 500
CANONICAL_FILES = {
    "user_query": "user_query.txt",
    "search_queries": "search_queries.txt",
    "intermediate_report": "intermediate_report.md",
    "final_report": "final_report.md",
}


def log(message: str) -> None:
    print(message, file=sys.stderr)


def read_text(path: Path, max_bytes: int | None = None) -> str:
    data = path.read_bytes()
    if max_bytes is not None:
        data = data[:max_bytes]
    return data.decode("utf-8", errors="replace")


def read_input_files(input_dir: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            log(f"Skipping large file: {path.relative_to(input_dir)}")
            continue
        try:
            content = read_text(path)
        except OSError as exc:
            log(f"Skipping unreadable file {path}: {exc}")
            continue
        if "\x00" in content:
            continue
        files[str(path.relative_to(input_dir))] = content
    return files


def make_file_previews(files: dict[str, str]) -> str:
    chunks = []
    for name, content in files.items():
        preview = content[:PREVIEW_CHARS].replace("\n", "\\n")
        chunks.append(f"FILE: {name}\nPREVIEW: {preview}")
    return "\n\n".join(chunks)


def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).resolve().parent / "prompts" / name
    return read_text(prompt_path)


def render_prompt(name: str, **values: object) -> str:
    prompt = load_prompt(name)
    for key, value in values.items():
        if not isinstance(value, str):
            value = json.dumps(value, indent=2, ensure_ascii=False)
        prompt = prompt.replace("{" + key + "}", value)
    return prompt


def api_config() -> tuple[str, str, str]:
    api_key = os.environ.get("EVAL_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set EVAL_API_KEY or OPENAI_API_KEY before running the evaluator.")
    model = os.environ.get("EVAL_MODEL", DEFAULT_MODEL)
    base = os.environ.get("EVAL_API_BASE", DEFAULT_API_BASE).rstrip("/")
    return api_key, model, base


def call_llm(prompt: str, *, retries: int = 1) -> str:
    provider = os.environ.get("EVAL_PROVIDER", "openai").lower()
    if provider == "agy":
        return call_agy(prompt, retries=retries)

    api_key, model, base = api_config()
    url = f"{base}/chat/completions"
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "You are a precise evaluator. Return only the requested output."},
            {"role": "user", "content": prompt},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
        except (urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"LLM call failed: {last_error}")


def call_agy(prompt: str, *, retries: int = 1) -> str:
    """Call Antigravity CLI in print mode."""
    model = os.environ.get("EVAL_MODEL", DEFAULT_AGY_MODEL)
    timeout = os.environ.get("EVAL_AGY_TIMEOUT", "20m")
    command = [
        "agy",
        "--print",
        "--print-timeout",
        timeout,
        "--model",
        model,
        prompt,
    ]
    last_error: str | None = None
    for attempt in range(retries + 1):
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            return completed.stdout
        last_error = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        if attempt < retries:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"agy call failed: {last_error}")


def parse_json(text: str) -> object:
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.S | re.I)
    if fenced:
        stripped = fenced.group(1).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", stripped, flags=re.S)
        if match:
            return json.loads(match.group(1))
        raise


def ask_json(prompt: str, fallback: object) -> object:
    try:
        response = call_llm(prompt, retries=1)
        return parse_json(response)
    except Exception as exc:
        log(f"LLM/JSON error: {exc}")
        if "response" in locals():
            snippet = " ".join(response.strip().split())[:500]
            log(f"Raw model output starts: {snippet}")
        return fallback


def heuristic_classify_files(files: dict[str, str]) -> dict[str, str | None]:
    """Best-effort classifier used when the judge model returns invalid JSON."""
    result: dict[str, str | None] = {
        "user_query": None,
        "search_queries": None,
        "intermediate_report": None,
        "final_report": None,
    }
    for name, content in files.items():
        lower_name = name.lower()
        lower_content = content[:5000].lower()
        if result["user_query"] is None and ("user_query" in lower_name or "input_query" in lower_name):
            result["user_query"] = name
        if result["search_queries"] is None and (
            "sample search queries" in lower_name
            or ("searched scispace" in lower_content and "searched pubmed" in lower_content)
        ):
            result["search_queries"] = name
        if result["final_report"] is None and (
            "final" in lower_name
            or ("report" in lower_name and "## references" in lower_content)
            or ("## references" in lower_content and re.search(r"\[\d+\]", content))
        ):
            result["final_report"] = name
        if result["intermediate_report"] is None and (
            "insight" in lower_name
            or "intermediate" in lower_name
            or (lower_name.endswith(".md") and "## tl;dr" in lower_content and "## references" not in lower_content)
        ):
            result["intermediate_report"] = name

    if result["user_query"] is None:
        short_text_files = [
            name for name, content in files.items()
            if len(content.strip()) < 500 and not name.lower().endswith((".csv", ".py"))
        ]
        if short_text_files:
            result["user_query"] = short_text_files[0]
    return result


def canonical_classification(files: dict[str, str]) -> dict[str, str | None] | None:
    if all(name in files for name in CANONICAL_FILES.values()):
        return dict(CANONICAL_FILES)
    return None


def classify_files(files: dict[str, str], cli_query: str | None) -> dict[str, str | None]:
    canonical = canonical_classification(files)
    if canonical is not None:
        if cli_query:
            canonical["user_query"] = "__cli_query__.txt"
        return canonical

    if cli_query:
        synthetic = dict(files)
        synthetic["__cli_query__.txt"] = cli_query
        files = synthetic
    prompt = render_prompt("00_classify_files.md", file_previews=make_file_previews(files))
    result = ask_json(prompt, {})
    if not isinstance(result, dict):
        result = {}
    out = {
        "user_query": result.get("user_query"),
        "search_queries": result.get("search_queries"),
        "intermediate_report": result.get("intermediate_report"),
        "final_report": result.get("final_report"),
    }
    if cli_query:
        out["user_query"] = "__cli_query__.txt"
    normalized = {k: (v if isinstance(v, str) else None) for k, v in out.items()}
    fallback = heuristic_classify_files(files)
    for role, value in fallback.items():
        if normalized.get(role) is None:
            normalized[role] = value
    return normalized


def get_content(files: dict[str, str], classification: dict[str, str | None], role: str, cli_query: str | None) -> str | None:
    name = classification.get(role)
    if role == "user_query" and name == "__cli_query__.txt":
        return cli_query
    if not name:
        return None
    return files.get(name)


def clean_search_queries(raw_log: str) -> list[dict[str, str]]:
    result = ask_json(render_prompt("01_clean_search_queries.md", raw_log=raw_log), [])
    if isinstance(result, list) and result:
        return result
    return heuristic_clean_search_queries(raw_log)


def load_clean_search_queries(files: dict[str, str]) -> list[dict[str, str]] | None:
    raw = files.get("search_queries.json")
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        log(f"Invalid search_queries.json; falling back to text cleanup: {exc}")
        return None
    if not isinstance(parsed, list):
        log("Invalid search_queries.json; expected a JSON array.")
        return None
    cleaned = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        channel = item.get("channel")
        query = item.get("query")
        if isinstance(channel, str) and isinstance(query, str) and query.strip():
            cleaned.append({"channel": channel, "query": query})
    return cleaned or None


def heuristic_clean_search_queries(raw_log: str) -> list[dict[str, str]]:
    """Extract common 'Searched <channel> / query / N Papers' blocks."""
    queries: list[dict[str, str]] = []
    lines = [line.strip() for line in raw_log.splitlines()]
    for idx, line in enumerate(lines):
        if not line.lower().startswith("searched "):
            continue
        channel = line[len("Searched ") :].strip()
        for candidate in lines[idx + 1 : idx + 5]:
            if not candidate:
                continue
            if re.fullmatch(r"\d+\s+papers?", candidate, flags=re.I):
                continue
            if candidate.lower().startswith(("searched ", "no relevant", "now i'll", "combined and reranked")):
                break
            queries.append({"channel": channel, "query": candidate})
            break
    return queries


def extract_intents(query: str) -> list[dict[str, str]]:
    result = ask_json(render_prompt("02_extract_intents.md", query=query), [])
    return result if isinstance(result, list) else []


def stage1_coverage(intents: list[dict[str, str]], search_queries: list[dict[str, str]]) -> dict[str, object]:
    result = ask_json(
        render_prompt("03_stage1_intent_coverage.md", intents=intents, search_queries=search_queries),
        {"intents": []},
    )
    return result if isinstance(result, dict) else {"intents": []}


def stage2_directional(intents: list[dict[str, str]], report_text: str) -> dict[str, object]:
    result = ask_json(
        render_prompt("04_stage2_directional.md", intents=intents, report_text=report_text),
        {"intents": [], "drift": []},
    )
    return result if isinstance(result, dict) else {"intents": [], "drift": []}


def stage3_extract_claims(report_text: str) -> list[dict[str, object]]:
    result = ask_json(render_prompt("07_stage3_extract_claims.md", report_text=report_text), [])
    return result if isinstance(result, list) else []


def strip_tags(value: str) -> str:
    value = html.unescape(value)
    return re.sub(r"<[^>]+>", " ", value).strip()


def parse_references(report_text: str) -> dict[int, dict[str, str]]:
    refs: dict[int, dict[str, str]] = {}
    marker = re.search(r"^##+\s+(?:\d+\.\s+)?References\s*$", report_text, flags=re.I | re.M)
    if not marker:
        return refs
    ref_text = report_text[marker.end() :]
    matches = list(re.finditer(r"^\[(\d+)\]\s+(.*?)(?=^\[\d+\]\s+|\Z)", ref_text, flags=re.M | re.S))
    for match in matches:
        ref_id = int(match.group(1))
        text = " ".join(match.group(2).split())
        doi_match = re.search(r"(?:https?://doi\.org/|doi:\s*)(10\.\S+)", text, flags=re.I)
        url_match = re.search(r"https?://\S+", text)
        doi = doi_match.group(1).rstrip(".,)") if doi_match else ""
        url = url_match.group(0).rstrip(".,)") if url_match else ""
        title = text
        quoted = re.search(r'"([^"]+)"', text)
        if quoted:
            title = quoted.group(1)
        refs[ref_id] = {"id": str(ref_id), "text": text, "title": title, "doi": doi, "url": url}
    return refs


def http_json(url: str, timeout: int = 10) -> dict[str, object] | None:
    request = urllib.request.Request(url, headers={"User-Agent": "scispace-evals/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None


def fetch_crossref(doi: str) -> str | None:
    encoded = urllib.parse.quote(doi, safe="")
    data = http_json(f"https://api.crossref.org/works/{encoded}")
    if not data:
        return None
    message = data.get("message")
    if not isinstance(message, dict):
        return None
    title = " ".join(message.get("title") or [])
    abstract = message.get("abstract")
    parts = []
    if title:
        parts.append(f"Title: {title}")
    if isinstance(abstract, str) and abstract.strip():
        parts.append(f"Abstract: {strip_tags(abstract)}")
    return "\n".join(parts) or None


def fetch_semantic_scholar(doi: str) -> str | None:
    encoded = urllib.parse.quote(f"DOI:{doi}", safe=":")
    url = f"https://api.semanticscholar.org/graph/v1/paper/{encoded}?fields=title,abstract"
    data = http_json(url)
    if not data:
        return None
    title = data.get("title")
    abstract = data.get("abstract")
    parts = []
    if isinstance(title, str) and title:
        parts.append(f"Title: {title}")
    if isinstance(abstract, str) and abstract:
        parts.append(f"Abstract: {abstract}")
    return "\n".join(parts) or None



def load_local_csv_cache(files: dict[str, str]) -> dict[str, str]:
    import csv
    import io
    cache = {}
    for name, content in files.items():
        if not name.endswith(".csv"):
            continue
        try:
            f = io.StringIO(content)
            reader = csv.DictReader(f)
            for row in reader:
                doi = row.get("DOI", "").strip()
                if not doi:
                    continue
                # Normalize DOI
                doi_match = re.search(r"(10\.\S+)", doi, flags=re.I)
                if doi_match:
                    doi = doi_match.group(1).rstrip(".,)")
                else:
                    continue
                
                title = row.get("Paper Title", "").strip()
                abstract = row.get("Abstract", "").strip()
                parts = []
                if title:
                    parts.append(f"Title: {title}")
                if abstract:
                    parts.append(f"Abstract: {abstract}")
                if parts:
                    cache[doi] = "\n".join(parts)
        except Exception as exc:
            log(f"Failed to parse CSV {name}: {exc}")
    return cache


def find_and_parse_consolidated_csv(files: dict[str, str]) -> list[dict[str, str]] | None:
    import csv
    import io
    required_cols = {"Study Design and Population", "Key Findings on Adherence Accuracy or Outcomes", "Limitations and Gaps"}
    for name, content in files.items():
        if not name.endswith(".csv"):
            continue
        try:
            f = io.StringIO(content)
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                continue
            field_set = set(reader.fieldnames)
            normalized_fields = {re.sub(r'[\s,]+', '', col).lower() for col in field_set}
            normalized_reqs = {re.sub(r'[\s,]+', '', col).lower() for col in required_cols}
            if len(normalized_reqs.intersection(normalized_fields)) >= 2:
                rows = []
                for row in reader:
                    rows.append(row)
                return rows
        except Exception as exc:
            log(f"Failed to parse consolidated CSV {name}: {exc}")
    return None


def evaluate_data_extraction(rows: list[dict[str, str]]) -> dict[str, object]:
    criteria_cols = ["Study Design and Population", "Key Findings on Adherence Accuracy or Outcomes", "Limitations and Gaps"]
    results = []
    supported = 0
    total = 0
    
    # Verify the top 5 papers as a representative sample
    papers_to_check = rows[:5]
    for idx, row in enumerate(papers_to_check):
        paper_title = row.get("Paper Title", "Unknown Title")
        abstract = row.get("Abstract", "").strip()
        if not abstract:
            # Fallback to relevance explanation if abstract column is empty
            abstract = row.get("Relevance", "")
        
        for col in criteria_cols:
            cell_value = row.get(col, "").strip()
            if not cell_value:
                continue
            total += 1
            prompt = render_prompt(
                "05_verify_data_extraction.md",
                criteria_name=col,
                cell_value=cell_value,
                paper_title=paper_title,
                paper_abstract=abstract[:4000]
            )
            res = ask_json(prompt, {"verdict": "unsupported", "reason": "Execution failure"})
            verdict = str(res.get("verdict", "unsupported")).lower()
            if verdict == "supported":
                supported += 1
            results.append({
                "paper": paper_title,
                "criteria": col,
                "value": cell_value,
                "verdict": verdict,
                "reason": res.get("reason", "")
            })
            
    return {
        "score": pct(supported, total),
        "supported": supported,
        "total": total,
        "details": results
    }


def evaluate_synthesis_faithfulness(claims: list[dict[str, object]], rows: list[dict[str, str]]) -> dict[str, object]:
    table_summary_lines = []
    for idx, row in enumerate(rows[:10]):
        title = row.get("Paper Title", "Unknown Title")
        findings = row.get("Key Findings on Adherence Accuracy or Outcomes", "").strip()
        design = row.get("Study Design and Population", "").strip()
        limitations = row.get("Limitations and Gaps", "").strip()
        table_summary_lines.append(
            f"Paper [{idx+1}]: {title}\n"
            f"  - Study Design: {design}\n"
            f"  - Key Findings: {findings}\n"
            f"  - Limitations: {limitations}"
        )
    table_rows_text = "\n\n".join(table_summary_lines)
    
    results = []
    supported = 0
    total = 0
    
    # Check top 10 claims
    claims_to_check = claims[:10]
    for claim in claims_to_check:
        claim_text = claim.get("claim_text", "")
        if not claim_text:
            continue
        total += 1
        prompt = render_prompt(
            "06_verify_synthesis_faithfulness.md",
            claim_text=claim_text,
            table_rows=table_rows_text
        )
        res = ask_json(prompt, {"verdict": "unsupported", "reason": "Execution failure"})
        verdict = str(res.get("verdict", "unsupported")).lower()
        if verdict == "supported":
            supported += 1
        results.append({
            "claim": claim_text,
            "verdict": verdict,
            "reason": res.get("reason", "")
        })
        
    return {
        "score": pct(supported, total),
        "supported": supported,
        "total": total,
        "details": results
    }


def source_text_for_citations(citation_ids: list[int], refs: dict[int, dict[str, str]], cache: dict[str, str]) -> str | None:
    chunks = []
    for citation_id in citation_ids:
        ref = refs.get(citation_id)
        if not ref:
            continue
        doi = ref.get("doi", "")
        content = None
        if doi:
            if doi not in cache:
                cache[doi] = fetch_crossref(doi) or fetch_semantic_scholar(doi) or ""
            content = cache[doi]
        if not content:
            content = f"Reference [{citation_id}]: {ref.get('text', '')}"
        chunks.append(content)
    return "\n\n".join(chunks) if chunks else None


def normalize_citation_ids(value: object) -> list[int]:
    if not isinstance(value, list):
        return []
    ids = []
    for item in value:
        try:
            ids.append(int(item))
        except (TypeError, ValueError):
            continue
    return ids


def ground_claim(claim: dict[str, object], refs: dict[int, dict[str, str]], cache: dict[str, str]) -> dict[str, object]:
    citation_ids = normalize_citation_ids(claim.get("citation_ids"))
    if not citation_ids and claim.get("is_common_knowledge") is True:
        return {
            "claim_text": claim.get("claim_text", ""),
            "citation_ids": citation_ids,
            "verdict": "common_knowledge",
            "reason": "Claim was marked as common knowledge by the claim extractor and is not scored.",
            "source_says": "",
        }
    if not citation_ids:
        return {
            "claim_text": claim.get("claim_text", ""),
            "citation_ids": citation_ids,
            "verdict": "uncited",
            "reason": "Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.",
            "source_says": "No citation attached.",
        }
    source_text = source_text_for_citations(citation_ids, refs, cache)
    if not source_text:
        return {
            "claim_text": claim.get("claim_text", ""),
            "citation_ids": citation_ids,
            "verdict": "not_verifiable",
            "reason": "No cited source could be matched for this claim.",
            "source_says": "",
        }
    result = ask_json(
        render_prompt(
            "08_stage3_ground_claim.md",
            claim_text=str(claim.get("claim_text", "")),
            citation_ids=citation_ids,
            paper_content=source_text[:12_000],
        ),
        {"verdict": "not_verifiable", "reason": "LLM judgment failed.", "source_says": ""},
    )
    if not isinstance(result, dict):
        result = {"verdict": "not_verifiable", "reason": "LLM judgment failed.", "source_says": ""}
    return {
        "claim_text": claim.get("claim_text", ""),
        "citation_ids": citation_ids,
        "verdict": str(result.get("verdict", "not_verifiable")).lower(),
        "reason": result.get("reason", ""),
        "source_says": result.get("source_says", ""),
    }


def pct(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else round((numerator / denominator) * 100, 1)


def generate_scorecard(details: dict[str, object]) -> str:
    lines = [
        "HALLUCINATION EVAL SCORECARD",
        "=============================",
        "",
    ]

    stage1 = details.get("stage1") if isinstance(details.get("stage1"), dict) else None
    if stage1:
        intents = stage1.get("intents", [])
        intents = intents if isinstance(intents, list) else []
        covered = [i for i in intents if isinstance(i, dict) and i.get("covered") is True]
        lines += [
            "Stage 1: Query Hallucination",
            f"  Intent Coverage ............... {pct(len(covered), len(intents))}%     ({len(covered)}/{len(intents)} intents covered)",
            "",
        ]
        for intent in intents:
            if isinstance(intent, dict) and intent.get("covered") is not True:
                lines += [
                    f"  X MISSED INTENT: \"{intent.get('intent', '')}\"",
                    f"    {intent.get('reason', '')}",
                    "",
                ]
        covered_examples = [i for i in intents if isinstance(i, dict) and i.get("covered") is True][:3]
        if covered_examples:
            lines += ["  Covered evidence examples:"]
            for intent in covered_examples:
                lines += [
                    f"    - {intent.get('intent', '')}: {intent.get('reason', '')}",
                ]
            lines.append("")
    else:
        lines += ["Stage 1: Query Hallucination", "  Skipped: missing query or search log.", ""]

    stage2 = details.get("stage2") if isinstance(details.get("stage2"), dict) else None
    data_ext = details.get("data_extraction") if isinstance(details.get("data_extraction"), dict) else None
    synth_faith = details.get("synthesis_faithfulness") if isinstance(details.get("synthesis_faithfulness"), dict) else None

    if stage2 or data_ext or synth_faith:
        lines += ["Stage 2: Directional Faithfulness & Data Accuracy"]
        if stage2:
            intents = stage2.get("intents", [])
            intents = intents if isinstance(intents, list) else []
            addressed = 0.0
            for intent in intents:
                if not isinstance(intent, dict):
                    continue
                status = str(intent.get("status", "")).lower()
                if status == "addressed":
                    addressed += 1
                elif status == "partially":
                    addressed += 0.5
            drift = stage2.get("drift", [])
            drift = drift if isinstance(drift, list) else []
            addressed_count = sum(1 for i in intents if isinstance(i, dict) and str(i.get("status", "")).lower() == "addressed")
            drift_label = "drift detected" if drift else "no drift"
            lines += [
                f"  Directional Alignment ......... {pct(addressed, len(intents))}%     ({addressed_count}/{len(intents)} fully addressed, {drift_label})",
            ]
        if data_ext:
            lines += [
                f"  Data Extraction Accuracy ...... {data_ext.get('score', 0.0)}%     ({data_ext.get('supported', 0)}/{data_ext.get('total', 0)} criteria cells accurate to papers)",
            ]
        if synth_faith:
            lines += [
                f"  Synthesis Faithfulness ........ {synth_faith.get('score', 0.0)}%     ({synth_faith.get('supported', 0)}/{synth_faith.get('total', 0)} report claims faithful to table)",
            ]
        lines += [""]

        if stage2:
            for intent in intents:
                if isinstance(intent, dict) and str(intent.get("status", "")).lower() != "addressed":
                    lines += [
                        f"  X {str(intent.get('status', 'missing')).upper()}: \"{intent.get('intent', '')}\"",
                        f"    {intent.get('reason', '')}",
                        "",
                    ]
            for item in drift:
                if isinstance(item, dict):
                    lines += [
                        f"  X DRIFT: \"{item.get('topic', '')}\"",
                        f"    {item.get('reason', '')}",
                        "",
                    ]
        if data_ext:
            for item in data_ext.get("details", []):
                verdict = str(item.get("verdict", "")).lower()
                if verdict in {"unsupported", "contradicted", "overstated"}:
                    lines += [
                        f"  X EXTRACTION {verdict.upper()}:",
                        f"    Paper: \"{item.get('paper', '')}\"",
                        f"    Criteria: \"{item.get('criteria', '')}\"",
                        f"    Cell: \"{item.get('value', '')}\"",
                        f"    -> {item.get('reason', '')}",
                        "",
                    ]
        if synth_faith:
            for item in synth_faith.get("details", []):
                verdict = str(item.get("verdict", "")).lower()
                if verdict in {"unsupported", "contradicted", "overstated"}:
                    lines += [
                        f"  X SYNTHESIS {verdict.upper()}:",
                        f"    Report Claim: \"{item.get('claim', '')}\"",
                        f"    -> {item.get('reason', '')}",
                        "",
                    ]

        if stage2:
            addressed_examples = [
                i for i in intents
                if isinstance(i, dict) and str(i.get("status", "")).lower() == "addressed"
            ][:3]
            if addressed_examples:
                lines += ["  Alignment evidence examples:"]
                for intent in addressed_examples:
                    lines += [
                        f"    - {intent.get('intent', '')}: {intent.get('reason', '')}",
                    ]
                lines.append("")
    else:
        lines += ["Stage 2: Directional Faithfulness & Data Accuracy", "  Skipped: missing intermediate report and consolidated table.", ""]

    stage3 = details.get("stage3") if isinstance(details.get("stage3"), list) else None
    if stage3 is not None:
        scored = [
            c for c in stage3
            if isinstance(c, dict) and c.get("verdict") != "common_knowledge"
        ]
        cited_verifiable = [
            c for c in scored
            if c.get("verdict") not in {"not_verifiable", "uncited"}
        ]
        supported = [c for c in scored if c.get("verdict") == "supported"]
        cited_supported = [c for c in cited_verifiable if c.get("verdict") == "supported"]
        counts = {
            label: 0
            for label in [
                "supported",
                "unsupported",
                "contradicted",
                "overstated",
                "uncited",
                "not_verifiable",
                "common_knowledge",
            ]
        }
        for claim in stage3:
            if isinstance(claim, dict):
                verdict = str(claim.get("verdict", "not_verifiable")).lower()
                counts[verdict] = counts.get(verdict, 0) + 1
        lines += [
            "Stage 3: Claim-Level Fact-Checking",
            f"  Claim Reliability ............. {pct(len(supported), len(scored))}%     ({len(supported)}/{len(scored)} non-common factual claims supported)",
            f"  Cited Grounding Rate .......... {pct(len(cited_supported), len(cited_verifiable))}%     ({len(cited_supported)}/{len(cited_verifiable)} cited verifiable claims supported)",
            f"    - Supported ................. {counts.get('supported', 0)}",
            f"    - Unsupported ............... {counts.get('unsupported', 0)}",
            f"    - Contradicted .............. {counts.get('contradicted', 0)}",
            f"    - Overstated ................ {counts.get('overstated', 0)}",
            f"    - Uncited factual claims .... {counts.get('uncited', 0)}",
            f"    - Not verifiable ............ {counts.get('not_verifiable', 0)}",
            f"    - Common knowledge .......... {counts.get('common_knowledge', 0)}",
            "",
        ]
        for claim in stage3:
            if not isinstance(claim, dict):
                continue
            verdict = str(claim.get("verdict", "")).lower()
            if verdict in {"unsupported", "contradicted", "overstated", "uncited"}:
                source_says = claim.get("source_says", "")
                source_line = f"    Source says: \"{source_says}\"" if verdict != "uncited" else "    Citation: none attached"
                lines += [
                    f"  X {verdict.upper()}:",
                    f"    Claim: \"{claim.get('claim_text', '')}\"",
                    source_line,
                    f"    -> {claim.get('reason', '')}",
                    "",
                ]
        supported_examples = [c for c in stage3 if isinstance(c, dict) and c.get("verdict") == "supported"][:3]
        if supported_examples:
            lines += ["  Supported examples:"]
            for claim in supported_examples:
                lines += [
                    f"    - Claim: \"{claim.get('claim_text', '')}\"",
                    f"      Source says: \"{claim.get('source_says', '')}\"",
                    f"      Reason: {claim.get('reason', '')}",
                ]
            lines.append("")
    else:
        stage3_status = details.get("stage3_status")
        if details.get("status") == "running" and isinstance(stage3_status, str):
            lines += ["Stage 3: Claim-Level Fact-Checking", f"  Pending: {stage3_status}.", ""]
        else:
            lines += ["Stage 3: Claim-Level Fact-Checking", "  Skipped: missing final report.", ""]


    # Append Cumulative Metrics Summary
    summary_lines = [
        "",
        "=====================================================================",
        "CUMULATIVE METRICS SUMMARY",
        "=====================================================================",
    ]
    
    if stage1:
        intents = stage1.get("intents", [])
        intents = intents if isinstance(intents, list) else []
        covered = [i for i in intents if isinstance(i, dict) and i.get("covered") is True]
        summary_lines.append(f"Stage 1: Intent Coverage .............................. {pct(len(covered), len(intents))}%")
    else:
        summary_lines.append("Stage 1: Intent Coverage .............................. Skipped")
        
    if stage2:
        intents = stage2.get("intents", [])
        intents = intents if isinstance(intents, list) else []
        addressed = 0.0
        for intent in intents:
            if not isinstance(intent, dict):
                continue
            status = str(intent.get("status", "")).lower()
            if status == "addressed":
                addressed += 1
            elif status == "partially":
                addressed += 0.5
        summary_lines.append(f"Stage 2: Directional Alignment ........................ {pct(addressed, len(intents))}%")
    else:
        summary_lines.append("Stage 2: Directional Alignment ........................ Skipped")

    if data_ext:
        summary_lines.append(f"Stage 2: Data Extraction Accuracy ..................... {data_ext.get('score', 0.0)}%")
    else:
        summary_lines.append("Stage 2: Data Extraction Accuracy ..................... Skipped/No Table")
        
    if synth_faith:
        summary_lines.append(f"Stage 2: Synthesis Faithfulness ....................... {synth_faith.get('score', 0.0)}%")
    else:
        summary_lines.append("Stage 2: Synthesis Faithfulness ....................... Skipped/No Table")

    stage3 = details.get("stage3") if isinstance(details.get("stage3"), list) else None
    if stage3 is not None:
        scored = [c for c in stage3 if isinstance(c, dict) and c.get("verdict") != "common_knowledge"]
        supported = [c for c in scored if c.get("verdict") == "supported"]
        cited_verifiable = [c for c in scored if c.get("verdict") not in {"not_verifiable", "uncited"}]
        cited_supported = [c for c in cited_verifiable if c.get("verdict") == "supported"]
        summary_lines.append(f"Stage 3: Claim Reliability ........................... {pct(len(supported), len(scored))}%")
        summary_lines.append(f"Stage 3: Cited Grounding Rate ......................... {pct(len(cited_supported), len(cited_verifiable))}%")
    else:
        summary_lines.append("Stage 3: Claim Reliability ........................... Skipped")
        summary_lines.append("Stage 3: Cited Grounding Rate ......................... Skipped")
        
    summary_lines.append("=====================================================================")
    summary_lines.append("")
    
    lines += summary_lines

    return "\n".join(lines).rstrip() + "\n"



def write_outputs(details: dict[str, object], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    scorecard = generate_scorecard(details)
    (output_dir / "scorecard.md").write_text(scorecard, encoding="utf-8")
    (output_dir / "detailed_log.json").write_text(json.dumps(details, indent=2, ensure_ascii=False), encoding="utf-8")


def run(input_dir: Path, cli_query: str | None, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = read_input_files(input_dir)
    log(f"Read {len(files)} files from {input_dir}")

    log("Step 0: classifying files")
    classification = classify_files(files, cli_query)

    query = get_content(files, classification, "user_query", cli_query)
    search_log = get_content(files, classification, "search_queries", cli_query)
    intermediate = get_content(files, classification, "intermediate_report", cli_query)
    final_report = get_content(files, classification, "final_report", cli_query)

    details: dict[str, object] = {
        "status": "running",
        "classification": classification,
        "search_queries": [],
        "intents": [],
        "stage1": None,
        "stage2": None,
        "stage3": None,
        "stage3_status": None,
    }
    write_outputs(details, output_dir)

    intents: list[dict[str, str]] = []
    if query and search_log:
        precleaned_queries = load_clean_search_queries(files)
        if precleaned_queries is not None:
            log("Step 0: using pre-cleaned search_queries.json")
            search_queries = precleaned_queries
        else:
            log("Step 0: cleaning search queries")
            search_queries = clean_search_queries(search_log)
        details["search_queries"] = search_queries
        write_outputs(details, output_dir)
        log("Stage 1: extracting intents")
        intents = extract_intents(query)
        details["intents"] = intents
        write_outputs(details, output_dir)
        if intents:
            log("Stage 1: checking query coverage")
            details["stage1"] = stage1_coverage(intents, search_queries)
            write_outputs(details, output_dir)
        else:
            log("Stage 1 skipped: intent extraction did not produce valid LLM output")
    else:
        log("Stage 1 skipped: missing user query or search query log")

    if intents and intermediate:
        log("Stage 2: checking directional alignment")
        details["stage2"] = stage2_directional(intents, intermediate)
        write_outputs(details, output_dir)
    # Stage 2 extensions
    details["data_extraction"] = None
    details["synthesis_faithfulness"] = None
    
    csv_rows = find_and_parse_consolidated_csv(files)
    if csv_rows:
        log("Stage 2: evaluating Data Extraction Accuracy (table vs. abstracts)")
        details["data_extraction"] = evaluate_data_extraction(csv_rows)
        write_outputs(details, output_dir)

    else:
        log("Stage 2 skipped: missing intents or intermediate report")

    if final_report:
        log("Stage 3: extracting claims")
        details["stage3_status"] = "extracting claims from final report"
        write_outputs(details, output_dir)
        claims = stage3_extract_claims(final_report)
        details["stage3_claims"] = claims
        if csv_rows:
            log("Stage 2: evaluating Synthesis Faithfulness (report claims vs. table)")
            details["synthesis_faithfulness"] = evaluate_synthesis_faithfulness(claims, csv_rows)
            write_outputs(details, output_dir)

        details["stage3"] = []
        details["stage3_status"] = f"grounding 0/{len(claims)} claims"
        write_outputs(details, output_dir)
        refs = parse_references(final_report)
        log(f"Stage 3: grounding {len(claims)} claims against {len(refs)} references")
        cache = load_local_csv_cache(files)
        log(f"Loaded {len(cache)} local papers from CSV files into cache.")
        from concurrent.futures import ThreadPoolExecutor, as_completed
        grounded = [None] * len(claims)
        log("Grounding claims in parallel (10 workers)...")
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_idx = {executor.submit(ground_claim, claim, refs, cache): i for i, claim in enumerate(claims)}
            completed_count = 0
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                grounded[idx] = future.result()
                completed_count += 1
                details["stage3"] = [g for g in grounded if g is not None]
                details["stage3_status"] = f"grounding {completed_count}/{len(claims)} claims"
                write_outputs(details, output_dir)
                if completed_count % 10 == 0 or completed_count == len(claims):
                    log(f"Stage 3: processed {completed_count}/{len(claims)} claims")
    else:
        log("Stage 3 skipped: missing final report")

    details["status"] = "complete"
    details["stage3_status"] = "complete"
    write_outputs(details, output_dir)
    return details



def load_env_file() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip("'\"")


def main() -> int:
    load_env_file()
    parser = argparse.ArgumentParser(description="Evaluate hallucination in a SciSpace report-writing run.")
    parser.add_argument("input_folder", type=Path, help="Folder containing files from one SciSpace run.")
    parser.add_argument("--query", help="User query text. Overrides/injects a query file for classification.")
    parser.add_argument("--output", type=Path, default=Path("output"), help="Output folder for scorecard and detailed log.")
    args = parser.parse_args()

    try:
        details = run(args.input_folder, args.query, args.output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(generate_scorecard(details))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
