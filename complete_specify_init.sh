#!/bin/bash
# Script to complete specify initialization without interactive prompts

set -e

PROJECT_DIR="/home/josh/moto-scraper-v1"
cd "$PROJECT_DIR"

echo "Completing Specify initialization for moto-scraper-v1..."

# Create .specify/config.json if it doesn't exist
if [ ! -f ".specify/config.json" ]; then
    echo "Creating .specify/config.json..."
    mkdir -p .specify
    cat > .specify/config.json << 'EOF'
{
  "project_name": "moto-scraper-v1",
  "ai_assistant": "cursor-agent",
  "initialized": true,
  "version": "1.0.0"
}
EOF
    echo "✅ Created .specify/config.json"
else
    echo "⚠️  .specify/config.json already exists"
fi

# Update constitution if it's still a template
if grep -q "\[PROJECT_NAME\]" .specify/memory/constitution.md 2>/dev/null; then
    echo "Updating constitution.md..."
    sed -i 's/\[PROJECT_NAME\]/Motorcycle OEM Web-Crawler/g' .specify/memory/constitution.md
    echo "✅ Updated constitution.md"
else
    echo "✅ Constitution already configured"
fi

# Create .cursorrules if it doesn't exist (for Cursor integration)
if [ ! -f ".cursorrules" ]; then
    echo "Creating .cursorrules for Cursor..."
    cat > .cursorrules << 'EOF'
# Motorcycle OEM Web-Crawler - Cursor Rules

This project uses Spec Kit for development. Follow the specifications in:
- SPECIFICATION.md
- plan.md  
- tasks.md
- .specify/memory/constitution.md

## Key Rules
1. Follow the constitution and specifications strictly
2. All measurements must be in metric units
3. No guessing values - use None for missing data
4. Rate limit: minimum 3 seconds between requests
5. Human-like navigation with proper delays
EOF
    echo "✅ Created .cursorrules"
else
    echo "✅ .cursorrules already exists"
fi

echo ""
echo "✅ Specify initialization complete!"
echo ""
echo "Project: moto-scraper-v1"
echo "AI Assistant: Cursor (cursor-agent)"
echo ""
echo "You can now use Spec Kit features in Cursor."


