---
name: sync-docs
description: Sync and update documentation across all Astrabit-CPT repositories efficiently using parallel subagents.
---

# Sync Documentation

Synchronize documentation across all Astrabit-CPT repositories. Fetches the latest repository list, clones/updates repos, and updates documentation for repos with code changes.

## Usage

```
/sync-docs [options]
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
- If exists: `git pull --shallow` (update)
- If new: `git clone --depth 1` (shallow clone for speed)

**Shallow clones** save bandwidth and time - only fetch latest commit.

### 3. Detect Changes

Compare last commit date with last documentation update:

```python
if last_commit_date > last_doc_update_date:
    needs_update = True
```

Skips repos without code changes since last doc run (unless `--force` is used).

### 4. Parallel Processing

Launch subagents IN PARALLEL to process repositories:

```
Subagent 1: "Generate/update docs for repo-a"
Subagent 2: "Generate/update docs for repo-b"
Subagent 3: "Generate/update docs for repo-c"
Subagent 4: "Generate/update docs for repo-d"
Subagent 5: "Generate/update docs for repo-e"
... (continue with batches of 5)
```

Each subagent:
1. Analyzes the repository
2. Generates/updates `catalog-info.yaml` if needed
3. Generates/updates `README.md`, `INTEGRATIONS.md` if needed
4. Returns summary of changes

### 5. Generate Report

Produces a summary report:

```markdown
# Documentation Sync Report

## Summary
- Processed: 47 repos
- Updated: 12 repos (code changes detected)
- Skipped: 35 repos (no changes)
- Failed: 0 repos

## Updated Repositories

| Repo | Changes | Docs Updated |
|------|---------|--------------|
| order-service | New endpoints | README.md, API.md, catalog-info.yaml |
| user-service | New dependency | INTEGRATIONS.md, catalog-info.yaml |
| trade-service | New events | catalog-info.yaml |

## Skipped Repositories
[35 repos with no changes]

## Failed Repositories
[None]
```

## Efficiency Optimizations

| Optimization | Benefit |
|--------------|---------|
| Shallow clones (`--depth 1`) | 10-100x faster than full clones |
| Parallel subagents | 5x faster than sequential |
| Skip unchanged repos | Avoids unnecessary work |
| Incremental updates | Only modifies changed files |
| Metadata caching | Reuses catalog-info.yaml when unchanged |

## Scripts

### fetch-repos.sh

Fetch repository list from GitHub:

```bash
./commands/sync-docs/scripts/fetch-repos.sh --org Astrabit-CPT
```

Output: JSON list of repositories with name, url, updatedAt.

### sync-all.py

Orchestrate the full sync process:

```bash
./commands/sync-docs/scripts/sync-all.py --org Astrabit-CPT --repos-dir ./repos
```

This script:
1. Calls fetch-repos.sh to get repo list
2. Clones/updates repositories
3. Detects changes
4. Launches parallel subagents
5. Generates report

## Example Output

```
$ /sync-docs

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
| api-gateway | New route to payment-service | catalog-info.yaml, routes table |
| trade-service | New events: trade.executed | catalog-info.yaml |
```

## Troubleshooting

**Issue:** `gh: command not found`
- **Solution:** Install GitHub CLI and run `gh auth login`

**Issue:** Authentication failed
- **Solution:** Run `gh auth logout` then `gh auth login` again

**Issue:** Parallel processing too slow
- **Solution:** Adjust `--parallel` based on your system (try 10 or 15)

**Issue:** Some repos fail to clone
- **Solution:** Check SSH key is added to GitHub account
