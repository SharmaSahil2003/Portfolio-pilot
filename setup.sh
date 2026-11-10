#!/usr/bin/env bash
# Creates the .claude/skills symlink so Claude Code discovers the PortfolioPilot skill.
set -euo pipefail

if [ ! -d ".agents/skills" ]; then
  echo "Run this from the project root (the folder containing .agents/)." >&2
  exit 1
fi

mkdir -p .claude
if [ -e ".claude/skills" ] || [ -L ".claude/skills" ]; then
  echo ".claude/skills already exists; leaving it unchanged."
else
  ln -s ../.agents/skills .claude/skills
  echo "Linked .claude/skills -> ../.agents/skills"
fi
