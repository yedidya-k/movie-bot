#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=".env"
FORCE="${1:-}"

if [ -f "$ENV_FILE" ] && [ "$FORCE" != "--force" ]; then
    echo "Error: $ENV_FILE already exists. Use --force to overwrite."
    exit 1
fi

echo "=== Movie Bot Setup ==="
echo ""

# Check Python 3.11+
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo "Error: Python 3.11+ required"
    exit 1
fi

# Check pip is available
if ! python3 -m pip --version &>/dev/null; then
    echo "Error: pip is not installed. Install pip for Python 3 first."
    exit 1
fi

# Prompts with defaults
read -p "Download path [./downloads/]: " DOWNLOAD_PATH
DOWNLOAD_PATH="${DOWNLOAD_PATH:-./downloads/}"

while true; do
    read -p "API_ID: " API_ID
    if [[ "$API_ID" =~ ^[0-9]+$ ]]; then
        break
    fi
    echo "Error: API_ID must be a number"
done

while true; do
    read -p "API_HASH: " API_HASH
    if [ -n "$API_HASH" ]; then
        break
    fi
    echo "Error: API_HASH cannot be empty"
done

while true; do
    read -p "PHONE_NUMBER (e.g., +1234567890): " PHONE_NUMBER
    if [ -n "$PHONE_NUMBER" ]; then
        break
    fi
    echo "Error: PHONE_NUMBER cannot be empty"
done

while true; do
    read -p "GROUP_IDS (comma-separated, e.g., -100111,-100222): " GROUP_IDS
    if [ -z "$GROUP_IDS" ]; then
        echo "Error: GROUP_IDS cannot be empty"
        continue
    fi
    valid=true
    IFS=',' read -ra PARTS <<< "$GROUP_IDS"
    for part in "${PARTS[@]}"; do
        if ! [[ "$part" =~ ^-?[0-9]+$ ]]; then
            echo "Error: '$part' is not a valid group ID (must be an integer)"
            valid=false
            break
        fi
    done
    if [ "$valid" = true ]; then
        break
    fi
done
while true; do
    read -p "BRIDGE_GROUP_ID (optional): " BRIDGE_GROUP_ID
    if [ -z "$BRIDGE_GROUP_ID" ]; then
        break
    fi
    if [[ "$BRIDGE_GROUP_ID" =~ ^-?[0-9]+$ ]]; then
        break
    fi
    echo "Error: BRIDGE_GROUP_ID must be an integer"
done
while true; do
    read -p "BRIDGE_BOTS (comma-separated, e.g., @SerchtAsBot): " BRIDGE_BOTS
    if [ -z "$BRIDGE_BOTS" ]; then
        echo "Error: BRIDGE_BOTS cannot be empty"
        continue
    fi
    valid=true
    IFS=',' read -ra PARTS <<< "$BRIDGE_BOTS"
    for part in "${PARTS[@]}"; do
        trimmed=$(echo "$part" | xargs)
        if [ -z "$trimmed" ]; then
            echo "Error: empty bot username in list"
            valid=false
            break
        fi
        if [[ "$trimmed" != @* ]]; then
            echo "Error: '$trimmed' must start with @"
            valid=false
            break
        fi
    done
    if [ "$valid" = true ]; then
        break
    fi
done

# Write .env
cat > "$ENV_FILE" << EOF
DOWNLOAD_PATH=$DOWNLOAD_PATH
GROUP_IDS=$GROUP_IDS
BRIDGE_GROUP_ID=$BRIDGE_GROUP_ID
BRIDGE_BOTS=$BRIDGE_BOTS

API_ID=$API_ID
API_HASH=$API_HASH
PHONE_NUMBER=$PHONE_NUMBER
EOF

echo ".env written."
echo ""

# Create and use virtual environment (avoids externally-managed-environment errors)
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create download directory
mkdir -p "$DOWNLOAD_PATH"

echo ""
echo "=== Setup complete ==="
echo "Run: ./venv/bin/python main.py"
