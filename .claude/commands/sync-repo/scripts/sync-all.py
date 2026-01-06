#!/usr/bin/env python3
"""
Orchestrate parallel documentation sync across all repositories.

Usage: python sync-all.py [--org ORG] [--repos-dir DIR] [--parallel N]
"""

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import PR workflow for creating pull requests
sys.path.insert(0, str(Path(__file__).parent))
from pr_workflow import PRWorkflow, check_existing_pr, get_branch_name


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> str:
    """Run a command and return output."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )
    return result.stdout


def fetch_repos(org: str = "Astrabit-CPT") -> List[Dict[str, Any]]:
    """Fetch repository list from GitHub via gh CLI."""
    script_path = Path(__file__).parent / "fetch-repos.sh"
    if not script_path.exists():
        # Fallback: run gh directly
        output = run_command([
            "gh", "repo", list, org,
            "--json", "name,url,updatedAt,isArchived,visibility",
            "--limit", "500"
        ])
    else:
        output = run_command(["bash", str(script_path), org])

    try:
        repos = json.loads(output)
        return repos
    except json.JSONDecodeError:
        print(f"Error: Failed to parse repository list", file=sys.stderr)
        return []


def get_default_branch(repo_path: Path) -> str:
    """Get the default branch (main or master) for a repository."""
    # Try to get the default branch from origin
    result = run_command(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        cwd=repo_path
    )
    if result.returncode == 0 and result.stdout:
        # refs/remotes/origin/refs/heads/main -> main
        branch = result.stdout.strip().split("/")[-1]
        return branch

    # Fallback: check if main or master exists
    for branch in ["main", "master"]:
        result = run_command(
            ["git", "rev-parse", "--verify", f"origin/{branch}"],
            cwd=repo_path
        )
        if result.returncode == 0:
            return branch

    return "main"  # Default fallback


def clone_or_update_repo(repo: Dict[str, Any], repos_dir: Path) -> tuple[str, str]:
    """Clone or update a single repository. Returns (name, status)."""
    name = repo["name"]
    repo_path = repos_dir / name
    url = repo.get("url", "")

    try:
        if repo_path.exists():
            # Update existing repo
            # Step 1: Fetch all remotes
            result = run_command(
                ["git", "fetch", "origin"],
                cwd=repo_path
            )

            if result.returncode != 0:
                return name, "error (fetch failed)"

            # Step 2: Get the default branch
            default_branch = get_default_branch(repo_path)

            # Step 3: Reset to latest origin/default-branch
            result = run_command(
                ["git", "reset", "--hard", f"origin/{default_branch}"],
                cwd=repo_path
            )

            if result.returncode != 0:
                return name, f"error (reset to {default_branch} failed)"

            # Get last commit date and short hash
            date_output = run_command(
                ["git", "log", "-1", "--format=%h %ci"],
                cwd=repo_path
            )
            last_commit = date_output.strip() if date_output else ""

            return name, f"updated {default_branch} ({last_commit[:20]})"
        else:
            # Clone new repo (shallow, from default branch)
            # Use --single-branch to reduce size and ensure we track the default branch
            result = subprocess.run(
                ["git", "clone", "--depth", "1", "--single-branch", url, str(repo_path)],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                # Get the branch that was cloned
                branch_output = run_command(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=repo_path
                )
                branch = branch_output.strip() if branch_output else "unknown"
                return name, f"cloned ({branch})"
            else:
                return name, "error (clone failed)"
    except Exception as e:
        return name, f"error: {e}"


def clone_or_update_all(repos: List[Dict[str, Any]], repos_dir: Path,
                       parallel: int = 5) -> Dict[str, str]:
    """Clone or update all repositories in parallel."""
    results = {}
    total = len(repos)

    print(f"Cloning/updating {total} repositories...")

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {
            executor.submit(clone_or_update_repo, repo, repos_dir): repo["name"]
            for repo in repos
        }

        for i, future in enumerate(as_completed(futures), 1):
            name, status = future.result()
            results[name] = status
            print(f"  [{i}/{total}] {name}: {status}")

    return results


def get_last_commit_date(repo_path: Path) -> Optional[datetime]:
    """Get the last commit date for a repository."""
    try:
        output = run_command(
            ["git", "log", "-1", "--format=%ci"],
            cwd=repo_path
        )
        if output.strip():
            return datetime.fromisoformat(output.strip()[:19])
    except Exception:
        pass
    return None


def get_last_doc_update(repo_path: Path) -> Optional[datetime]:
    """Get the last modification date of documentation files."""
    doc_files = [
        "catalog-info.yaml",
        "README.md",
        "INTEGRATIONS.md",
        "ARCHITECTURE.md",
        "API.md",
    ]

    latest = None
    for doc_file in doc_files:
        file_path = repo_path / doc_file
        if file_path.exists():
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if latest is None or mtime > latest:
                latest = mtime

    return latest


def needs_update(repo_path: Path, force: bool = False) -> bool:
    """Check if a repository needs documentation update."""
    if force:
        return True

    last_commit = get_last_commit_date(repo_path)
    last_doc_update = get_last_doc_update(repo_path)

    if last_commit is None:
        return False
    if last_doc_update is None:
        return True

    return last_commit > last_doc_update


def process_repo_docs(name: str, repo_path: Path) -> Dict[str, Any]:
    """Process documentation for a single repository (placeholder for subagent)."""
    # In actual implementation, this would launch a subagent
    # For now, return a summary of what would be done

    result = {
        "name": name,
        "changes": [],
        "docs_updated": [],
    }

    # Check if catalog-info.yaml exists
    catalog_path = repo_path / "catalog-info.yaml"
    if not catalog_path.exists():
        result["changes"].append("No catalog-info.yaml - needs generation")
        result["docs_updated"].append("catalog-info.yaml (new)")

    # Check other docs
    for doc_file in ["README.md", "INTEGRATIONS.md"]:
        doc_path = repo_path / doc_file
        if not doc_path.exists():
            result["docs_updated"].append(f"{doc_file} (new)")

    return result


def sync_docs(repos: List[Dict[str, Any]], repos_dir: Path,
              parallel: int = 5, force: bool = False, dry_run: bool = False,
              org: str = "Astrabit-CPT", create_prs: bool = True) -> Dict[str, Any]:
    """Sync documentation across all repositories."""
    report = {
        "total": len(repos),
        "updated": [],  # PRs created or changes made
        "skipped": [],  # No changes needed or existing PRs
        "failed": [],   # Errors during processing
    }

    # Initialize PR workflow
    workflow = PRWorkflow(org, repos_dir) if create_prs else None

    # Find repos that need updates
    need_update = []
    for repo in repos:
        name = repo["name"]
        repo_path = repos_dir / name

        if not repo_path.exists():
            continue

        if needs_update(repo_path, force):
            need_update.append((name, repo_path))
        else:
            report["skipped"].append(name)

    if not need_update:
        return report

    print(f"\nProcessing {len(need_update)} repos with changes...")

    if create_prs:
        branch_name = get_branch_name()
        print(f"Using branch: {branch_name}")

    # Process in parallel (in real implementation, this would launch subagents)
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {
            executor.submit(process_repo_docs, name, path): (name, path)
            for name, path in need_update
        }

        for future in as_completed(futures):
            try:
                result = future.result()
                repo_name = result["name"]

                if not result["docs_updated"] and not result.get("changes"):
                    # No docs needed updating
                    report["skipped"].append(repo_name)
                    continue

                if create_prs and workflow:
                    # Check for existing PR
                    existing_pr = check_existing_pr(repo_name, org, workflow.branch_name)
                    if existing_pr:
                        report["skipped"].append(repo_name)
                        print(f"  {repo_name}: skipped (existing PR #{existing_pr['number']})")
                        continue

                    if dry_run:
                        # In dry run, just report what would happen
                        report["updated"].append({
                            "repo": repo_name,
                            "changes": result.get("changes", []),
                            "docs": result["docs_updated"],
                            "pr_url": f"https://github.com/{org}/{repo_name}/pull/dry-run",
                        })
                    else:
                        # TODO: Actually launch subagent to generate docs here
                        # For now, just report what would be done
                        report["updated"].append({
                            "repo": repo_name,
                            "changes": result.get("changes", []),
                            "docs": result["docs_updated"],
                            "pending_pr": True,  # PR would be created after docs generated
                        })
                else:
                    # No PR creation - just report
                    if dry_run:
                        report["updated"].append({
                            "repo": repo_name,
                            "changes": result.get("changes", []),
                            "docs": result["docs_updated"],
                        })
                    else:
                        report["updated"].append({
                            "repo": repo_name,
                            "changes": result.get("changes", []),
                            "docs": result["docs_updated"],
                        })
            except Exception as e:
                name, _ = futures[future]
                report["failed"].append({"repo": name, "error": str(e)})

    return report


def print_report(report: Dict[str, Any]):
    """Print the sync report."""
    print("\n" + "=" * 60)
    print("# Documentation Sync Report")
    print("=" * 60)
    print(f"\n## Summary")
    print(f"- Processed: {report['total']} repos")
    print(f"- Updated: {len(report['updated'])} repos")
    print(f"- Skipped: {len(report['skipped'])} repos")
    print(f"- Failed: {len(report['failed'])} repos")

    if report["updated"]:
        print(f"\n## Updated Repositories ({len(report['updated'])})")

        # Check if we have PR URLs to show
        has_prs = any("pr_url" in item or "pending_pr" in item for item in report["updated"])

        if has_prs:
            print("| Repo | Changes | PR |")
            print("|------|---------|-----|")
            for item in report["updated"]:
                changes = ", ".join(item.get("changes", ["Code changes"]))
                pr_info = item.get("pr_url", "Pending...")
                print(f"| {item['repo']} | {changes} | {pr_info} |")
        else:
            print("| Repo | Changes | Docs Updated |")
            print("|------|---------|--------------|")
            for item in report["updated"]:
                changes = ", ".join(item.get("changes", ["Code changes"]))
                docs = ", ".join(item.get("docs", ["N/A"]))
                print(f"| {item['repo']} | {changes} | {docs} |")

    if report["skipped"] and len(report["skipped"]) <= 10:
        print(f"\n## Skipped Repositories")
        for repo in report["skipped"]:
            print(f"- {repo}")
    elif report["skipped"]:
        print(f"\n## Skipped Repositories")
        print(f"{len(report['skipped'])} repos with no changes")

    if report["failed"]:
        print(f"\n## Failed Repositories")
        for item in report["failed"]:
            print(f"- {item['repo']}: {item.get('error', 'Unknown error')}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Sync documentation across all repositories"
    )
    parser.add_argument("--org", default="Astrabit-CPT",
                       help="GitHub organization")
    parser.add_argument("--repos-dir", default="repos",
                       help="Local repositories directory")
    parser.add_argument("--parallel", type=int, default=5,
                       help="Number of parallel processes")
    parser.add_argument("--force", action="store_true",
                       help="Update all repos, not just changed ones")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be updated without making changes")
    parser.add_argument("--no-pr", action="store_true",
                       help="Skip PR creation and only update local files")
    args = parser.parse_args()

    repos_dir = Path(args.repos_dir)
    repos_dir.mkdir(parents=True, exist_ok=True)

    create_prs = not args.no_pr

    # Fetch repository list
    print(f"Fetching repositories from {args.org}...")
    repos = fetch_repos(args.org)

    if not repos:
        print("No repositories found or error fetching list")
        return 1

    print(f"Found {len(repos)} repositories")

    if create_prs:
        branch_name = get_branch_name()
        print(f"PR branch: {branch_name}")

    # Clone/update all repos
    clone_results = clone_or_update_all(repos, repos_dir, args.parallel)

    # Count errors
    errors = sum(1 for status in clone_results.values() if "error" in status)

    if errors > 0:
        print(f"\nWarning: {errors} repos had errors during clone/update")

    # Sync documentation
    report = sync_docs(repos, repos_dir, args.parallel, args.force,
                      args.dry_run, args.org, create_prs)

    # Print report
    print_report(report)

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
