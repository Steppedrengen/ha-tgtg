#!/usr/bin/env bash
# ============================================================
# push_to_github.sh
# Run this once from inside the ha-tgtg/ folder to create
# the GitHub repo and push all files.
#
# Requirements: git, gh (GitHub CLI) — https://cli.github.com
# ============================================================

set -e

REPO_NAME="ha-tgtg"
DESCRIPTION="Too Good To Go custom integration for Home Assistant with distance-based sorting"

echo "→ Initialising git..."
git init
git add .
git commit -m "feat: initial release v1.0.0"

echo "→ Creating GitHub repository..."
gh repo create "$REPO_NAME" \
  --public \
  --description "$DESCRIPTION" \
  --push \
  --source=.

echo ""
echo "✅ Done! Your repo is live at:"
gh repo view --web
