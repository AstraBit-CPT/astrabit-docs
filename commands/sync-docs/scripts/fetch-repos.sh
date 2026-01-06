#!/usr/bin/env bash
#
# Fetch repository list from GitHub using gh CLI
#
# Usage: ./fetch-repos.sh [--org ORGANIZATION]
#
# Output: JSON with name, url, updatedAt, and isPrivate fields

set -euo pipefail

ORG="${1:-Astrabit-CPT}"
LIMIT="${2:-500}"

# Check if gh is available
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) not found" >&2
    echo "Install from: https://cli.github.com/" >&2
    echo "Then run: gh auth login" >&2
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with gh CLI" >&2
    echo "Run: gh auth login" >&2
    exit 1
fi

# Fetch repositories
gh repo list "$ORG" --json name,url,updatedAt,isArchived,visibility --limit "$LIMIT" \
    | jq '[.[] | select(.isArchived == false) | {
           name,
           url,
           updatedAt,
           private: (.visibility == "private")
       }]'
