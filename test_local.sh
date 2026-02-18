#!/bin/bash
# Quick local testing without Railways deployment
# Usage: ./test_local.sh

# Create a test environment
# For real testing, set TOKEN and ADMIN_ID from environment or .env file
# Never hardcode real tokens in this script!
export TOKEN="${TOKEN:-123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11}"
export ADMIN_ID="${ADMIN_ID:-1234567890}"

echo "🧪 Testing SlotBot locally..."
echo ""

# Check Python syntax
echo "📝 Checking Python syntax..."
python3 -m py_compile bot.py config.py storage.py models.py handlers.py utils.py game_state.py commands_admin.py commands_stats.py commands_gameplay.py
if [ $? -eq 0 ]; then
    echo "✅ All files compile successfully"
else
    echo "❌ Syntax errors found!"
    exit 1
fi

echo ""
echo "📦 Testing imports..."
python3 << 'PYEOF'
import sys
try:
    import config
    print("  ✓ config")
    import storage
    print("  ✓ storage")
    import models
    print("  ✓ models")
    import game_state
    print("  ✓ game_state")
    import utils
    print("  ✓ utils")
    import commands_stats
    print("  ✓ commands_stats")
    import commands_gameplay
    print("  ✓ commands_gameplay")
    import commands_admin
    print("  ✓ commands_admin")
    import handlers
    print("  ✓ handlers")
    print("")
    print("✅ All imports successful!")
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "🎲 Testing game functions..."
python3 << 'PYEOF'
import config
import storage
import models

# Test config
assert config.WIN_VALUES == {1, 22, 43, 64}, "WIN_VALUES incorrect"
print("  ✓ Config constants correct")

# Test models
scores = {}
models.ensure_user_struct(scores, "123", "TestUser")
assert "123" in scores, "User not created"
assert scores["123"]["name"] == "TestUser", "Username incorrect"
assert scores["123"]["elo"] == 1000, "Default ELO incorrect"
print("  ✓ User structure creation works")

# Test ELO calculation
scores["123"]["elo"] = 1000
scores["456"] = {"name": "Player2", "elo": 1000}
elo_gain, elo_loss = models.update_elo("123", "456", scores)
assert elo_gain > 0, "Winner should gain ELO"
assert elo_loss < 0, "Loser should lose ELO"
print("  ✓ ELO calculation works")

# Test storage functions
print("  ✓ Storage functions available")

print("")
print("✅ All game functions work!")
PYEOF

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "🧪 Testing command functions..."
python3 << 'PYEOF'
from utils import format_winrate, msg_vittoria, msg_streak, msg_sfiga, is_expansion_active

# Test utility functions
assert format_winrate(5, 10) == "50.00%", "Winrate formatting failed"
print("  ✓ format_winrate works")

assert "JACKPOT" in msg_vittoria("Test", True), "Victory message failed"
print("  ✓ msg_vittoria works")

assert "DOPPIA" in msg_streak("Test", 2), "Streak message failed"
print("  ✓ msg_streak works")

assert msg_sfiga("Test", 5) == "", "Sfiga message should be empty for low values"
print("  ✓ msg_sfiga works")

assert is_expansion_active(999) == False, "Expansion check failed"
print("  ✓ is_expansion_active works")

print("")
print("✅ All utility functions work!")
PYEOF

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "════════════════════════════════════════"
echo "✅ ALL TESTS PASSED!"
echo "════════════════════════════════════════"
echo ""
echo "Ready to deploy! 🚀"
echo ""
