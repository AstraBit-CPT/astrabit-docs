---
name: sync-repo
description: Sync documentation for a single AstraBit repository, creating a PR for changes. Use /sync-all for all repos.
dynamicArguments: true
---

# Sync Single Repository Documentation

Synchronize documentation for a single AstraBit repository. Creates a pull request for changes.

## Usage

```
/sync-repo <repository-name> [options]
/sync-repo user-service
/sync-repo order-service --force
/sync-repo trade-service --no-pr
```

## Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `repository-name` | Name of the repository to sync | Yes |

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--org` | GitHub organization | Astrabit-CPT |
| `--repos-dir` | Local repos directory | ./repos |
| `--force` | Update even if no changes detected | false |
| `--no-pr` | Skip PR creation and only update local files | false |

## Workflow

### 1. Fetch Repository Info

Uses GitHub CLI to fetch repository details:

```bash
gh repo view Astrabit-CPT/<repository-name> --json name,url,defaultBranchRef
```

**Prerequisite:** User must be authenticated with `gh auth login`.

### 2. Clone/Update Repository

**Existing repo:**
1. `git fetch origin` - Fetch latest from remote
2. `git reset --hard origin/{default-branch}` - Reset to latest commit

**New repo:**
1. `git clone --depth 1 --single-branch {url}` - Shallow clone

### 3. Detect Changes

Compare last commit date with last documentation update. Skips if no changes (unless `--force` is used).

### 4. Check for Existing PR

Checks if an open PR already exists from the doc sync workflow for today's branch (`chore/doc-sync-[date]`). Skips if an existing PR is found.

### 5. Update Documentation

Generates/updates documentation files:
- `catalog-info.yaml` - Service catalog metadata
- `README.md` - Repository overview
- `INTEGRATIONS.md` - Dependencies and integration points

### 6. Create PR (unless `--no-pr`)

1. Creates branch: `chore/doc-sync-[date]`
2. Commits documentation changes
3. Pushes branch to remote
4. Creates PR with standard title and labels

## PR Creation

When `--no-pr` is NOT used:

- **Branch name:** `chore/doc-sync-[date]` (e.g., `chore/doc-sync-2025-01-06`)
- **PR title:** `docs: Update documentation ([date])`
- **PR labels:** `documentation`, `automated`

## Example Output

```
$ /sync-repo user-service

Fetching repository info...
Found: user-service (default branch: main)

Cloning/updating...
✓ user-service (updated 2 hours ago)

Detecting changes...
New commits detected - documentation needs update

Checking for existing PRs...
No existing PR found for today's branch

Generating documentation...
✓ catalog-info.yaml updated
✓ README.md updated
✓ INTEGRATIONS.md unchanged

Creating PR...
✓ Branch created: chore/doc-sync-2025-01-06
✓ PR created: https://github.com/Astrabit-CPT/user-service/pull/142

# Sync Complete: user-service

## Changes
- Last commit: 2 hours ago
- Docs updated: Yes
- PR: https://github.com/Astrabit-CPT/user-service/pull/142

## Files Updated
- catalog-info.yaml (added kafka topics)
- README.md (added new endpoints)
```

## See Also

- `/sync-all` - Sync all repositories in parallel
