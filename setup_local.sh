#!/bin/bash
# Setup script for local development

echo "🔧 SlotBot Local Setup"
echo "====================="
echo ""

if [ -f .env.local ]; then
    echo "✅ .env.local already exists"
else
    echo "📝 Creating .env.local..."
    cat > .env.local << 'EOF'
# Local testing environment
# Add your REAL token here for local testing
# This file is in .gitignore - NEVER accidentally commit it!

TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ADMIN_ID=1234567890
EOF
    echo "✅ Created .env.local with safe placeholders"
    echo ""
    echo "📌 Next steps:"
    echo "   1. If you want to test locally with a real bot:"
    echo "      - Get your real token from @BotFather on Telegram"
    echo "      - Edit .env.local and paste the REAL TOKEN"
    echo "      - Then run: ./test_local.sh"
    echo ""
    echo "   2. For just running tests without a real bot:"
    echo "      - Just run: ./test_local.sh"
    echo "      - (It will use the safe placeholder token)"
    echo ""
fi

echo ""
echo "🧪 Testing the bot..."
./test_local.sh
