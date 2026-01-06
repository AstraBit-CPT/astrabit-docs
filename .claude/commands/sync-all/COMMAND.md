---
name: sync-all
description: Sync and update documentation for all AstraBit repositories in parallel.
---

# Sync All Repository Documentation

Synchronize documentation for all AstraBit repositories in parallel.

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

### 4. Parallel Processing

Launch subagents IN PARALLEL to process repositories (5 concurrent by default).

Each subagent:
1. Analyzes the repository
2. Generates/updates `catalog-info.yaml` if needed
3. Generates/updates `README.md`, `INTEGRATIONS.md` if needed
4. Returns summary of changes

### 5. Generate Report

Produces a summary report with processed, updated, skipped, and failed counts.

## Example Output

```
$ /sync-all

Fetching repositories from Astrabit-CPT...
Found 47 repositories

Cloning/updating repositories...
✓ api-gateway (updated)
✓ user-service (up to date)
✓ order-service (updated)
...
✓ notification-worker (cloned)

Detecting changes...
12 repos need documentation updates

Processing repos in parallel (5 concurrent)...
[████████████████████████████████████████] 100%

# Documentation Sync Report

## Summary
- Processed: 47 repos
- Updated: 12 repos
- Skipped: 35 repos
- Failed: 0 repos

## Updated Repositories

| Repo | Changes | Docs Updated |
|------|---------|--------------|
| order-service | New endpoints, new Kafka topic | README.md, catalog-info.yaml |
| user-service | New dependency on auth-service | INTEGRATIONS.md |
| api-gateway | New route to payment-service | catalog-info.yaml |
| trade-service | New events: trade.executed | catalog-info.yaml |
```

## Troubleshooting

**Issue:** `gh: command not found`
- **Solution:** Install GitHub CLI and run `gh auth login`

**Issue:** Authentication failed
- **Solution:** Run `gh auth logout` then `gh auth login` again

**Issue:** Parallel processing too slow
- **Solution:** Adjust `--parallel` based on your system (try 10 or 15)
