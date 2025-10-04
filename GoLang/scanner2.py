#!/usr/bin/env python3
"""
go_inspector.py
---------------
Performs Go code security inspection using:
- gosec
- staticcheck
- govulncheck

The tool clones a target repository, executes each analyzer,
prints recommendations directly to the console,
and saves minimal summary data to a single consolidated file.

Author: Friend Version (restructured variant)
"""

import os
import sys
import json
import time
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# ==================================================
# Utility Functions
# ==================================================

def tool_available(tool: str) -> bool:
    """Check if a tool is available in PATH."""
    return shutil.which(tool) is not None

def execute(cmd: list, cwd: str = None, timeout: int = 300) -> tuple[int, str, str]:
    """Execute a shell command and return code, stdout, stderr."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return proc.returncode, proc.stdout.decode(errors="ignore"), proc.stderr.decode(errors="ignore")
    except subprocess.TimeoutExpired:
        return 124, "", f"Timeout while running {' '.join(cmd)}"
    except Exception as e:
        return 127, "", str(e)

def git_clone(repo_url: str, dest: str) -> bool:
    """Clone a Git repository."""
    rc, out, err = execute(["git", "clone", repo_url, dest])
    if rc == 0:
        print("Repository cloned successfully.")
        return True
    else:
        print("Git clone failed:", err or out)
        return False

# ==================================================
# Parsing Helpers
# ==================================================

def parse_json_output(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None

def parse_gosec_output(raw: str) -> List[Dict[str, Any]]:
    data = parse_json_output(raw) or {}
    return data.get("Issues", [])

def parse_staticcheck_output(raw: str) -> List[Dict[str, Any]]:
    data = parse_json_output(raw)
    return data if isinstance(data, list) else []

def parse_govulncheck_output(output: str) -> list[dict]:
    findings = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue  # skip non-JSON lines

        # ensure it's a dictionary
        if not isinstance(entry, dict):
            continue

        # handle "Finding" key or direct structure
        finding = entry.get("Finding") if "Finding" in entry else entry
        if not isinstance(finding, dict):
            continue

        vuln_id = (
            finding.get("id")
            or finding.get("ID")
            or (finding.get("OSV") or {}).get("id")
            or (finding.get("osv") or {}).get("id")
        )

        package = None
        if "Module" in finding and isinstance(finding["Module"], dict):
            package = finding["Module"].get("Path") or finding["Module"].get("path")
        elif "Package" in finding and isinstance(finding["Package"], dict):
            package = finding["Package"].get("Path") or finding["Package"].get("path")

        if vuln_id or package:
            findings.append({
                "id": vuln_id,
                "package": package,
                "raw": finding
            })
    return findings


# ==================================================
# Suggestion Generators
# ==================================================

def suggest_gosec(rule: str) -> str:
    tips = {
        "G101": "Avoid hardcoded credentials; move them to env vars or secrets manager.",
        "G103": "Use parameterized queries to prevent SQL injection.",
        "G401": "Use crypto/rand for secure randomness.",
        "G402": "Enable TLS certificate validation."
    }
    return tips.get(rule, "General best practice: validate inputs and follow Go security guidelines.")

def suggest_staticcheck(code: str) -> str:
    tips = {
        "SA4006": "Remove unused variables to clean up code.",
        "SA9001": "Check error return values properly.",
        "ST1005": "Avoid capitalized error strings."
    }
    return tips.get(code, "Review the warning and improve code reliability.")

def suggest_vulnerability(vuln_id: str) -> str:
    if vuln_id.startswith("GO-"):
        return "Upgrade to latest module release fixing this issue."
    if vuln_id.startswith("CVE-"):
        return "Apply patched version to mitigate CVE."
    return "Review module advisory and upgrade dependencies."

# ==================================================
# Main Analyzer Logic
# ==================================================

def analyze_repo(repo_url: str) -> None:
    required = ["git", "gosec", "staticcheck", "govulncheck"]
    missing = [t for t in required if not tool_available(t)]
    if missing:
        print("⚠ Missing dependencies:", ", ".join(missing))
        print("Install required tools before running this scanner.")
        return

    temp_dir = tempfile.mkdtemp(prefix="goinsp-")
    try:
        if not git_clone(repo_url, temp_dir):
            return

        # --- Gosec ---
        print("\n[1] Running gosec...")
        rc, out, err = execute(["gosec", "-fmt=json", "./..."], cwd=temp_dir)
        gosec_issues = parse_gosec_output(out)
        for item in gosec_issues:
            print(f"→ {item.get('rule_id', 'N/A')} [{item.get('severity', 'N/A')}] {item.get('details', '')}")
            print("   Recommendation:", suggest_gosec(item.get("rule_id", "")))

        # --- Staticcheck ---
        print("\n[2] Running staticcheck...")
        rc, out, err = execute(["staticcheck", "-f=json", "./..."], cwd=temp_dir)
        issues = parse_staticcheck_output(out)
        for it in issues:
            code = it.get("code", "N/A")
            msg = it.get("message", "")
            print(f"→ {code}: {msg}")
            print("   Recommendation:", suggest_staticcheck(code))

        # --- Govulncheck ---
        print("\n[3] Running govulncheck...")
        rc, out, err = execute(["govulncheck", "-json", "./..."], cwd=temp_dir)
        vulns = parse_govulncheck_output(out)
        for v in vulns:
            vid = v.get("id") or (v.get("OSV") or {}).get("id")
            pkg = (v.get("Module") or {}).get("Path")
            print(f"→ Vulnerability {vid} in package {pkg}")
            print("   Recommendation:", suggest_vulnerability(vid or ""))

        # --- Summary ---
        print("\n========== SUMMARY ==========")
        print(f"gosec issues: {len(gosec_issues)}")
        print(f"staticcheck issues: {len(issues)}")
        print(f"govulncheck findings: {len(vulns)}")
        print("==============================")

        # Save minimal summary to file
        result_summary = {
            "repository": repo_url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "gosec": len(gosec_issues),
                "staticcheck": len(issues),
                "govulncheck": len(vulns)
            }
        }
        filename = f"inspection_summary_{int(time.time())}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result_summary, f, indent=2)
        print(f"\nSummary saved to {filename}")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# ==================================================
# Entry Point
# ==================================================

def main():
    if len(sys.argv) < 2:
        repo = input("Enter repository URL: ").strip()
    else:
        repo = sys.argv[1]

    if not repo:
        print("No repository provided.")
        return

    print(f"\nStarting Go inspection for: {repo}")
    analyze_repo(repo)

if __name__ == "__main__":
    main()
