#!/usr/bin/env python3
"""
go_scanner_py.py
-----------------
Clones a Go repository, runs security and static analysis tools:
- gosec
- staticcheck
- govulncheck

Parses JSON outputs, summarizes results, provides actionable recommendations,
and saves consolidated results to a timestamped JSON file.

Author: Piyush (improved version)
"""

import json
import shutil
import subprocess
import sys
import tempfile
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

# ----------------------
# Basic Helpers
# ----------------------

def check_tool(tool: str) -> bool:
    """Return True if tool is found on PATH."""
    return shutil.which(tool) is not None

def run(cmd: list, cwd: str = None, timeout: int = 300) -> tuple[int, str, str]:
    """
    Run a shell command with a timeout.
    Returns (returncode, stdout, stderr) decoded as UTF-8.
    """
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout
        )
        stdout = proc.stdout.decode("utf-8", errors="ignore")
        stderr = proc.stderr.decode("utf-8", errors="ignore")
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"Command timed out: {' '.join(cmd)}"
    except FileNotFoundError as e:
        return 127, "", str(e)

def clone_repo(repo_url: str, dest_dir: str) -> Tuple[bool, str]:
    """Clone repo_url into dest_dir. Returns (success, message)."""
    rc, out, err = run(["git", "clone", repo_url, dest_dir])
    if rc == 0:
        return True, out.strip()
    else:
        return False, err or out or f"git clone failed with code {rc}"

# ----------------------
# JSON Parsers
# ----------------------

def parse_gosec(json_text: str) -> List[Dict[str, Any]]:
    try:
        obj = json.loads(json_text)
    except json.JSONDecodeError:
        return []
    issues = obj.get("Issues") or obj.get("issues") or []
    parsed = []
    for it in issues:
        parsed.append({
            "rule_id": it.get("rule_id") or it.get("Rule"),
            "severity": it.get("severity"),
            "details": it.get("details") or it.get("detail") or it.get("message"),
            "file": it.get("file"),
            "line": it.get("line"),
        })
    return parsed

def parse_staticcheck(json_text: str) -> List[Dict[str, Any]]:
    try:
        arr = json.loads(json_text)
    except json.JSONDecodeError:
        return []
    if not isinstance(arr, list):
        return []
    parsed = []
    for it in arr:
        loc = it.get("location") or {}
        parsed.append({
            "code": it.get("code") or it.get("rule") or it.get("id"),
            "severity": it.get("severity") or "INFO",
            "message": it.get("message") or it.get("msg"),
            "file": loc.get("file"),
            "line": loc.get("line"),
        })
    return parsed

def parse_govulncheck(json_text: str) -> list[dict]:
    """
    Robust parser for govulncheck NDJSON output.
    Handles mixed entries (strings, dicts, and nested structures).
    """
    parsed = []

    for line in json_text.splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            doc = json.loads(line)
        except json.JSONDecodeError:
            continue  # skip invalid JSON lines

        # Ignore any non-dict entries (e.g. plain status messages)
        if not isinstance(doc, dict):
            continue

        # Some entries wrap data under "Finding"
        if "Finding" in doc and isinstance(doc["Finding"], dict):
            doc = doc["Finding"]

        # Ignore again if it's not a dict after unwrapping
        if not isinstance(doc, dict):
            continue

        vuln_id = (
            doc.get("id")
            or doc.get("ID")
            or (doc.get("OSV") or {}).get("id")
            or (doc.get("osv") or {}).get("id")
        )

        pkg = None
        if "Module" in doc and isinstance(doc["Module"], dict):
            pkg = doc["Module"].get("Path") or doc["Module"].get("path")
        elif "Package" in doc and isinstance(doc["Package"], dict):
            pkg = doc["Package"].get("Path") or doc["Package"].get("path")

        # Only record meaningful entries
        if vuln_id or pkg:
            parsed.append({
                "id": vuln_id,
                "package": pkg,
                "raw": doc
            })

    return parsed


# ----------------------
# Suggestions / Recommendations
# ----------------------

GOSEC_SUGGESTIONS = {
    "G101": "Avoid hardcoded credentials; use environment variables or a secrets manager.",
    "G102": "Validate network addresses; avoid SSRF-like issues.",
    "G103": "Avoid SQL injection; use parameterized queries.",
    "G104": "Avoid shell injection; use sanitized exec.Command input.",
    "G301": "Avoid hardcoded cryptographic keys; store securely.",
    "G402": "Do not skip TLS verification; validate certificates properly.",
    "G501": "Use crypto/rand for cryptographically secure randomness.",
}

STATICCHECK_SUGGESTIONS = {
    "SA4006": "Remove or use the unused variable — likely dead code.",
    "SA1012": "Fix formatting issues flagged by staticcheck.",
    "ST1005": "Error string should not be capitalized.",
    "SA9001": "Check error return values to avoid unexpected failures.",
    "SA4011": "Replace deprecated/unsafe functions with recommended alternatives.",
}

# Dynamic fallback for CVEs or unknown vuln IDs
def suggestion_for_vuln(vuln_id: str) -> str:
    if vuln_id.startswith("GO-"):
        return "Update to the latest secure version of the affected module."
    elif vuln_id.startswith("CVE-"):
        return "Upgrade to a patched version that fixes this CVE."
    return "Check advisory details and update the dependency accordingly."

# ----------------------
# Summaries
# ----------------------

def summarize_gosec(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    print(f"\n1) gosec: {len(issues)} issue(s) found")
    summary = {"total": len(issues), "by_severity": {}, "items": []}
    for it in issues:
        sev = (it.get("severity") or "UNKNOWN").upper()
        summary["by_severity"].setdefault(sev, 0)
        summary["by_severity"][sev] += 1
        rule = it.get("rule_id")
        file, line, details = it.get("file") or "", it.get("line") or "", it.get("details") or ""
        print(f"  - [{sev}] {rule or 'N/A'}: {details} ({file}:{line})")
        suggestion = GOSEC_SUGGESTIONS.get(rule, "No specific recommendation.")
        print(f"      → Recommendation: {suggestion}")
        summary["items"].append({
            "rule": rule,
            "severity": sev,
            "details": details,
            "file": file,
            "line": line,
            "recommendation": suggestion,
        })
    return summary

def summarize_staticcheck(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    print(f"\n2) staticcheck: {len(issues)} issue(s) found")
    summary = {"total": len(issues), "items": []}
    for it in issues:
        code, msg = it.get("code") or "N/A", it.get("message") or ""
        file, line = it.get("file") or "", it.get("line") or ""
        print(f"  - [{code}] {msg} ({file}:{line})")
        suggestion = STATICCHECK_SUGGESTIONS.get(code, "No specific recommendation.")
        print(f"      → Recommendation: {suggestion}")
        summary["items"].append({
            "code": code,
            "message": msg,
            "file": file,
            "line": line,
            "recommendation": suggestion,
        })
    return summary

def summarize_govulncheck(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    meaningful = [f for f in findings if f.get("id") or f.get("package")]
    print(f"\n3) govulncheck: {len(meaningful)} vulnerability item(s) found")
    summary = {"total": len(meaningful), "items": []}
    for it in meaningful:
        vid, pkg = it.get("id"), it.get("package")
        suggestion = suggestion_for_vuln(vid)
        print(f"  - ID: {vid}, package: {pkg}")
        print(f"      → Recommendation: {suggestion}")
        summary["items"].append({
            "id": vid,
            "package": pkg,
            "recommendation": suggestion,
        })
    return summary

# ----------------------
# Orchestrator
# ----------------------

def run_scans_on_repo(repo_url: str, save_json: bool = True) -> Dict[str, Any]:
    tools = ["git", "gosec", "staticcheck", "govulncheck"]
    missing = [t for t in tools if not check_tool(t)]
    if missing:
        print(f"Missing tools: {', '.join(missing)}")
        print("Please install them and ensure they are on your PATH.")
        return {"error": f"missing tools: {missing}"}

    tmpdir = tempfile.mkdtemp(prefix="go-scan-")
    try:
        ok, msg = clone_repo(repo_url, tmpdir)
        if not ok:
            print(f"Failed to clone repo: {msg}")
            return {"error": msg}

        print("\nRepository cloned successfully.")

        # --- Gosec ---
        print("\nRunning gosec (JSON)...")
        rc, gosec_out, gosec_err = run(["gosec", "-fmt=json", "./..."], cwd=tmpdir)
        gosec_issues = parse_gosec(gosec_out if gosec_out else "")
        if rc not in (0, 1):
            print("gosec encountered issues:", gosec_err.strip())

        # --- Staticcheck ---
        print("\nRunning staticcheck (JSON)...")
        rc, static_out, static_err = run(["staticcheck", "-f=json", "./..."], cwd=tmpdir)
        if rc not in (0, 1):  # 1 = issues found
            print("staticcheck encountered errors:", static_err.strip())
        static_issues = parse_staticcheck(static_out)

        # --- Govulncheck ---
        print("\nRunning govulncheck (JSON)...")
        rc, govuln_out, govuln_err = run(["govulncheck", "-json", "./..."], cwd=tmpdir)
        govuln_findings = parse_govulncheck(govuln_out if govuln_out else "")
        if rc not in (0, 1):
            print("govulncheck error:", govuln_err.strip())

        # --- Summaries ---
        gosec_summary = summarize_gosec(gosec_issues)
        static_summary = summarize_staticcheck(static_issues)
        vuln_summary = summarize_govulncheck(govuln_findings)

        result = {
            "repo": repo_url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "gosec": gosec_summary,
            "staticcheck": static_summary,
            "govulncheck": vuln_summary,
        }

        if save_json:
            repo_name = Path(repo_url).stem or "repo"
            out_path = Path.cwd() / f"scan_results_{repo_name}_{int(time.time())}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to {out_path}")

        # --- Final Summary ---
        print("\n===== SUMMARY =====")
        print(f"Gosec: {gosec_summary['total']} issue(s)")
        print(f"Staticcheck: {static_summary['total']} issue(s)")
        print(f"Govulncheck: {vuln_summary['total']} finding(s)")
        print("======================\n")

        return result

    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass

# ----------------------
# CLI Entry
# ----------------------

def main():
    if len(sys.argv) >= 2:
        repo = sys.argv[1]
    else:
        repo = input("Enter GitHub repo URL (e.g. https://github.com/user/repo.git): ").strip()
    if not repo:
        print("No repository URL provided.")
        sys.exit(1)

    print(f"\nStarting scan for repo: {repo}")
    res = run_scans_on_repo(repo)
    if res.get("error"):
        print("Scan finished with errors:", res["error"])
    else:
        print("Scan completed successfully.")

if __name__ == "__main__":
    main()
