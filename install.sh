#!/usr/bin/env bash
# Install the dv-generate Claude Code plugin.
# Usage: curl -fsSL https://raw.githubusercontent.com/Haddley/dv-generate/main/install.sh | bash

set -euo pipefail

INSTALL_DIR="$HOME/.claude/plugins/local/dv-generate"
PLUGINS_JSON="$HOME/.claude/plugins/installed_plugins.json"
REPO="https://github.com/Haddley/dv-generate.git"
PLUGIN_KEY="dv-generate@local"

echo "Installing dv-generate Claude Code plugin..."

# Clone or update
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Updating existing install at $INSTALL_DIR"
  git -C "$INSTALL_DIR" pull --ff-only
else
  echo "Cloning into $INSTALL_DIR"
  git clone "$REPO" "$INSTALL_DIR"
fi

# Register in installed_plugins.json if not already present
if ! grep -q "$PLUGIN_KEY" "$PLUGINS_JSON" 2>/dev/null; then
  echo "Registering plugin in $PLUGINS_JSON"
  # Use python3 to edit JSON safely
  python3 - <<PYEOF
import json, sys, datetime

path = "$PLUGINS_JSON"
try:
    with open(path) as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {"version": 2, "plugins": {}}

now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
data.setdefault("plugins", {})["$PLUGIN_KEY"] = [
    {
        "scope": "local",
        "installPath": "$INSTALL_DIR",
        "version": "1.0.0",
        "installedAt": now,
        "lastUpdated": now,
    }
]

with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")

print("Registered.")
PYEOF
else
  echo "Already registered in $PLUGINS_JSON"
fi

# Symlink into ~/.claude/skills/ so Claude Code discovers it
SKILLS_DIR="$HOME/.claude/skills"
SKILL_LINK="$SKILLS_DIR/dv-generate"
mkdir -p "$SKILLS_DIR"
if [ -L "$SKILL_LINK" ]; then
  echo "Skill symlink already exists at $SKILL_LINK"
elif [ -e "$SKILL_LINK" ]; then
  echo "Warning: $SKILL_LINK exists but is not a symlink — skipping"
else
  ln -s "$INSTALL_DIR/skills/dv-generate" "$SKILL_LINK"
  echo "Linked skill to $SKILL_LINK"
fi

echo ""
echo "Done. Restart Claude Code to activate the dv-generate skill."
