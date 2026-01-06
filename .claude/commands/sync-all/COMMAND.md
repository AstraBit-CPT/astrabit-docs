---
name: sync-all
description: Sync and update documentation for all AstraBit repositories in parallel, creating PRs for changes.
---

# Sync All Repository Documentation

Synchronize documentation for all AstraBit repositories in parallel. Creates pull requests for each repository with documentation changes.

## Usage

```
/sync-all [options]
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--org` | GitHub organization | Astrabit-CPT |
| `--repos-dir` | Local repos directory | ./repos |
| `--dry-run` | Show what would be updated without making changes | false |
| `--force` | Update all repos, not just changed ones | false |
| `--parallel` | Number of parallel subagents | 5 |
| `--no-pr` | Skip PR creation and only update local files | false |

## Workflow

### 1. Fetch Repository List

Uses GitHub CLI (`gh`) to fetch all repositories:

```bash
gh repo list Astrabit-CPT --json name,url,updatedAt --limit 500
```

**Prerequisite:** User must be authenticated with `gh auth login`.

### 2. Clone/Update Repositories

For each repository:

**Existing repos:**
1. `git fetch origin` - Fetch latest from remote
2. Detect default branch (main or master)
3. `git reset --hard origin/{default-branch}` - Reset to latest commit

**New repos:**
1. `git clone --depth 1 --single-branch {url}` - Shallow clone

### 3. Detect Changes

Compare last commit date with last documentation update. Skips repos without code changes since last doc run (unless `--force` is used).

### 4. Check for Existing PRs

Before processing each repository, checks if an open PR already exists from the doc sync workflow for today's branch (`chore/doc-sync-[date]`). Skips repos with existing PRs to avoid duplicates.

### 5. Parallel Processing

Launch subagents IN PARALLEL to process repositories (5 concurrent by default).

Each subagent:
1. Analyzes the repository
2. Generates/updates `catalog-info.yaml` if needed
3. Generates/updates `README.md`, `INTEGRATIONS.md` if needed
4. Creates a branch: `chore/doc-sync-[date]`
5. Commits the documentation changes
6. Pushes the branch to remote
7. Creates a PR with standard title and body
8. Returns summary with PR URL

### 6. Generate Report

Produces a summary report with processed, updated, skipped, and failed counts, including PR URLs.

## PR Creation

Each repository with documentation changes gets:

- **Branch name:** `chore/doc-sync-[date]` (e.g., `chore/doc-sync-2025-01-06`)
- **PR title:** `docs: Update documentation ([date])`
- **PR labels:** `documentation`, `automated`
- **PR body:** Includes list of changes and files modified

## Example Output

```
$ /sync-all

Fetching repositories from Astrabit-CPT...
Found 47 repositories
PR branch: chore/doc-sync-2025-01-06

Cloning/updating repositories...
✓ api-gateway (updated)
✓ user-service (up to date)
✓ order-service (updated)
...
✓ notification-worker (cloned)

Detecting changes...
12 repos need documentation updates
3 repos skipped (existing PRs)

Processing repos in parallel (5 concurrent)...

# Documentation Sync Report

## Summary
- Processed: 47 repos
- Updated: 9 repos
- Skipped: 38 repos
- Failed: 0 repos

## Updated Repositories

| Repo | Changes | PR |
|------|---------|-----|
| order-service | New endpoints, new Kafka topic | https://github.com/Astrabit-CPT/order-service/pull/123 |
| user-service | New dependency on auth-service | https://github.com/Astrabit-CPT/user-service/pull/124 |
| api-gateway | New route to payment-service | https://github.com/Astrabit-CPT/api-gateway/pull/125 |
```

## Troubleshooting

**Issue:** `gh: command not found`
- **Solution:** Install GitHub CLI and run `gh auth login`

**Issue:** Authentication failed
- **Solution:** Run `gh auth logout` then `gh auth login` again

**Issue:** Parallel processing too slow
- **Solution:** Adjust `--parallel` based on your system (try 10 or 15)

**Issue:** Don't want to create PRs
- **Solution:** Use `--no-pr` to only update local files without pushing or creating PRs
