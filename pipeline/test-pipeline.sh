#!/bin/bash
# Quick test script for EcoChiefs asset pipeline

set -e

echo "🧪 Testing EcoChiefs Asset Pipeline"
echo "===================================="

cd "$(dirname "$0")/registry"

# Initialize registry
echo ""
echo "1️⃣ Initializing registry..."
python3 registry.py init

# Create test assets directory
mkdir -p ../../assets/3d
echo "Created test assets directory"

# Query empty registry
echo ""
echo "2️⃣ Querying empty registry..."
python3 registry.py query

# Show identities
echo ""
echo "3️⃣ Checking pre-loaded identities..."
if command -v sqlite3 &> /dev/null; then
    sqlite3 registry.db "SELECT * FROM identities;"
else
    python3 -c "import sqlite3; conn = sqlite3.connect('registry.db'); print('\\n'.join([f'{r[0]}: {r[1]}' for r in conn.execute('SELECT identity_id, name FROM identities')])); conn.close()"
fi

echo ""
echo "✅ Registry initialized successfully!"
echo ""
echo "Next steps:"
echo "  1. Add GLB files to assets/3d/"
echo "  2. Run: python3 registry.py ingest ../../assets/3d --identity ecochief.taurus --tool meshy"
echo "  3. Approve assets and publish to web"
echo ""
echo "See pipeline/README.md for full documentation."
