#!/usr/bin/env python3
"""
Detect domain and owner for repositories based on patterns and contributors.

Usage: python detect-metadata.py <repo_path> <repo_name>
Output: JSON with detected domain and owner
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional


# Domain patterns based on repo name prefixes/suffixes
DOMAIN_PATTERNS = {
    "trading": [
        "*gateway", "*service", "order-log", "trade-pair", "exchange",
        "tradingview", "copy", "bot", "portfolio", "position", "strategy",
        "signal", "commission", "promo-code", "payment", "nexus"
    ],
    "user": [
        "user-*", "glob-*", "kyc"
    ],
    "product": [
        "product-*"
    ],
    "infrastructure": [
        "devops", "*-iac", "docker-compose", "concourse", "proxy-manager",
        "event-bus", "uptime-watcher", "migrate-db", "*-shared"
    ],
    "data": [
        "public-data", "kline-crawler", "exchange-data", "indicator",
        "geometry", "ml-*", "*-adapter", "database-schema"
    ],
    "frontend": [
        "*-frontend", "*-web", "*-app", "*-panel", "web", "adex-*",
        "glob-*", "charting-library"
    ],
    "integrations": [
        "discord", "zammad", "wordpress", "mailhog", "keycloak"
    ],
    "platform": [
        "defi", "staking", "nodejs-http-proxy", "vps-proxy"
    ],
    "internal": [
        "ab-test", "ab-internal", "local-testing", "research-and-development",
        "microservice-local"
    ],
    "documentation": [
        "wiki", "docs"
    ]
}

# Team mappings based on repo patterns or common ownership
TEAM_PATTERNS = {
    "trading-team": [
        "*gateway", "*service", "exchange", "tradingview", "bot",
        "strategy", "signal", "commission", "position", "portfolio"
    ],
    "backend-team": [
        "user-*", "product-*", "payment", "kyc", "promo-code"
    ],
    "frontend-team": [
        "*-frontend", "*-web", "*-app", "*-panel", "adex-*", "glob-*"
    ],
    "infrastructure-team": [
        "devops", "*-iac", "docker-compose", "concourse"
    ],
    "data-team": [
        "*data", "*crawler", "indicator", "ml-*", "geometry"
    ],
    "platform-team": [
        "defi", "staking", "*proxy"
    ]
}


def match_pattern(name: str, patterns: list) -> bool:
    """Check if a name matches any pattern in the list."""
    for pattern in patterns:
        if "*" in pattern:
            # Convert glob pattern to regex
            regex = "^" + pattern.replace("*", ".*") + "$"
            if re.match(regex, name, re.IGNORECASE):
                return True
        elif pattern.lower() in name.lower():
            return True
    return False


def detect_domain_from_name(repo_name: str) -> str:
    """Detect domain from repository name patterns."""
    for domain, patterns in DOMAIN_PATTERNS.items():
        if match_pattern(repo_name, patterns):
            return domain
    return "unknown"


def detect_team_from_name(repo_name: str) -> str:
    """Detect team (owner) from repository name patterns."""
    for team, patterns in TEAM_PATTERNS.items():
        if match_pattern(repo_name, patterns):
            return team
    return "unknown"


def get_contributors(repo_path: Path) -> list:
    """Get list of top contributors to the repository."""
    try:
        result = subprocess.run(
            ["git", "log", "--pretty=format:%an", "--since=1 year ago"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return []

        # Count commits per author
        contributors = {}
        for line in result.stdout.strip().split("\n"):
            if line:
                contributors[line] = contributors.get(line, 0) + 1

        # Sort by commit count
        sorted_contributors = sorted(
            contributors.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Return top 5
        return [c[0] for c in sorted_contributors[:5]]
    except Exception:
        return []


def detect_from_readme(repo_path: Path) -> Dict[str, str]:
    """Try to detect domain/owner from existing README."""
    readme_path = repo_path / "README.md"
    if not readme_path.exists():
        return {}

    try:
        content = readme_path.read_text()

        # Look for team mentions
        team_keywords = {
            "trading": ["trading", "trade", "orders", "execution"],
            "backend": ["backend", "api", "service"],
            "frontend": ["frontend", "ui", "web", "react", "vue"],
            "infrastructure": ["devops", "infrastructure", "deployment"],
        }

        # Simple keyword detection
        detected = {}
        for team, keywords in team_keywords.items():
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    detected["domain"] = team
                    break
            if "domain" in detected:
                break

        return detected
    except Exception:
        return {}


def detect_from_package_json(repo_path: Path) -> Dict[str, str]:
    """Try to detect info from package.json."""
    package_json = repo_path / "package.json"
    if not package_json.exists():
        return {}

    try:
        content = package_json.read_text()
        data = json.loads(content)

        detected = {}

        # Check if it's a frontend app
        if any(dependency in str(data.get("dependencies", {}))
               for dependency in ["react", "vue", "angular", "next", "nuxt"]):
            detected["category"] = "frontend"

        return detected
    except Exception:
        return {}


def detect_metadata(repo_path: Path, repo_name: str) -> Dict:
    """Detect domain and owner for a repository."""
    # Start with name-based detection
    domain = detect_domain_from_name(repo_name)
    team = detect_team_from_name(repo_name)

    # Try to improve with README analysis
    readme_info = detect_from_readme(repo_path)
    if readme_info.get("domain") and readme_info["domain"] != "unknown":
        domain = readme_info["domain"]

    # Try package.json
    package_info = detect_from_package_json(repo_path)
    if package_info.get("category"):
        domain = package_info["category"]

    # Get contributors for owner reference
    contributors = get_contributors(repo_path)

    # Map team names to GitHub team names if possible
    owner_map = {
        "trading-team": "AstraBit-CPT/trading",
        "backend-team": "AstraBit-CPT/backend",
        "frontend-team": "AstraBit-CPT/frontend",
        "infrastructure-team": "AstraBit-CPT/devops",
        "data-team": "AstraBit-CPT/data",
        "platform-team": "AstraBit-CPT/platform",
    }

    owner = owner_map.get(team, team)

    return {
        "domain": domain,
        "owner": owner,
        "team": team,
        "top_contributors": contributors,
        "detection_method": "name_pattern" if not readme_info else "readme_analysis"
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: detect-metadata.py <repo_path> <repo_name>", file=sys.stderr)
        return 1

    repo_path = Path(sys.argv[1])
    repo_name = sys.argv[2]

    if not repo_path.exists():
        print(f"Error: Path {repo_path} does not exist", file=sys.stderr)
        return 1

    metadata = detect_metadata(repo_path, repo_name)
    print(json.dumps(metadata, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
