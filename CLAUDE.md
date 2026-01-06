# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a **Claude Code plugin** for managing and synchronizing documentation across AstraBit's microservice architecture. It provides commands and skills for:

1. **Repository Synchronization** - Cloning/updating repos and generating documentation
2. **Documentation Generation** - README, API docs, architecture docs, integration guides
3. **Service Catalog Metadata** - `catalog-info.yaml` files for architecture visualization
4. **Architecture Views** - Dependency graphs, request flows, event topology

## Key Concepts

### Repository Organization

- **`repos/`** - Cloned AstraBit repositories (gitignored, managed by sync commands)
- **`.claude/`** - Claude Code plugin structure (auto-discovered):
  - **`commands/`** - Slash commands (`/sync-repo`, `/sync-all`)
  - **`skills/`** - Reusable workflows (repo-docs, repo-metadata, arch-view, etc.)

### Documentation Philosophy

All generated documentation must include **cross-repository integration points**. Every document should answer:
- Which other repositories does this repo depend on?
- Which repositories depend on this one?
- What external services are used?
- How do requests/events flow between services?

### Service Classification

Services are typed in `catalog-info.yaml`:
- **gateway** - Routes requests, minimal business logic
- **service** - Has APIs (provides) and dependencies (consumes)
- **worker** - Event consumers only, no HTTP routes
- **library** - Shared utilities, no consumed APIs
- **frontend** - UI applications
- **database** - Data stores

## Common Commands

| Command | Purpose |
|---------|---------|
| `/sync-repo <name>` | Sync single repository |
| `/sync-all` | Sync all repositories in parallel |

## Prerequisites

For sync commands to work, the user must be authenticated with GitHub CLI:
```bash
gh auth login
```

## Skills Reference

| Skill | When to Use |
|-------|-------------|
| **repo-docs** | Generate README, API docs, ARCHITECTURE.md, CONTRIBUTING.md |
| **repo-metadata** | Generate/update `catalog-info.yaml` service catalog metadata |
| **arch-view** | Generate dependency graphs, request flows, event topology from all repos |
| **doc-coauthoring** | Guide users through structured document creation workflow |
| **skill-creator** | Create new skills or update existing ones |

## Architecture Visualization Workflow

1. Use `/sync-all` to ensure all repos have `catalog-info.yaml`
2. Launch parallel subagents (5-10 concurrent) to read each repo's metadata
3. Aggregate into unified model: components, dependencies, events, routes
4. Generate requested view:
   - **Dependency Graph** - All services and their dependencies
   - **Request Flow** - Gateway routes through to backend services
   - **Event Topology** - Kafka topic producers/consumers
   - **Service Groupings** - Services grouped by domain/team

## Sync Command Workflow

For `/sync-repo` and `/sync-all`:

1. **Fetch** - Use `gh repo list` or `gh repo view` to get repo info
2. **Clone/Update** - Shallow clone or `git reset --hard` for existing
3. **Detect Changes** - Compare commit date vs last doc update
4. **Generate Docs** - Launch subagents to generate:
   - `catalog-info.yaml` (via repo-metadata skill)
   - `README.md`, `INTEGRATIONS.md` (via repo-docs skill)
5. **Report** - Summary of updated, skipped, failed repos

## Scripts

Scripts are in `.claude/commands/sync-repo/scripts/` and `.claude/skills/*/scripts/`:

- **`fetch-repos.sh`** - Fetch repo list from GitHub
- **`sync-all.py`** - Orchestrate parallel repo sync
- **`aggregate-metadata.py`** - Collect all catalog-info.yaml files
- **`generate-mermaid.py`** - Convert metadata to Mermaid diagrams
- **`analyze-repo-structure.py`** - Analyze repo for documentation
- **`find-integration-points.py`** - Scan for cross-repo references
- **`generate-metadata.py`** - Generate catalog-info.yaml

Scripts can be executed without reading into context to save tokens.

## Gitignore Rules

- `repos/` - Cloned repositories are ephemeral
- `aggregated.json`, `*.aggregated.json` - Generated metadata aggregates
- Standard IDE, Python, Node, OS cache files
