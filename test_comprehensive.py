#!/usr/bin/env python3
"""
Comprehensive test suite for SlotBot
Tests all commands, handlers, and game logic
"""
import os
import sys
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Setup environment
os.environ['TOKEN'] = '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'
os.environ['ADMIN_ID'] = '1234567890'

# Clean test data files
for f in ['scores.json', 'users.json', 'duels.json']:
    if os.path.exists(f):
        os.remove(f)

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors = []
    
    def add_pass(self, name):
        self.passed += 1
        print(f"   ✓ {name}")
    
    def add_fail(self, name, error):
        self.failed += 1
        self.errors.append((name, error))
        print(f"   ❌ {name}: {str(error)[:50]}")
    
    def add_warning(self, name, msg):
        self.warnings += 1
        print(f"   ⚠️  {name}: {msg}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"Passed:  {self.passed}/{total}")
        print(f"Failed:  {self.failed}/{total}")
        print(f"Warnings: {self.warnings}")
        
        if self.errors:
            print(f"\n❌ Errors:")
            for name, error in self.errors[:5]:
                print(f"   • {name}: {error}")
        
        print(f"{'='*50}\n")
        
        return self.failed == 0

async def test_imports():
    """Test all imports work"""
    results = TestResults()
    print("\n📦 IMPORT TESTS")
    print("="*50)
    
    try:
        import config
        results.add_pass("config module")
    except Exception as e:
        results.add_fail("config", e)
    
    try:
        import storage
        results.add_pass("storage module")
    except Exception as e:
        results.add_fail("storage", e)
    
    try:
        import models
        results.add_pass("models module")
    except Exception as e:
        results.add_fail("models", e)
    
    try:
        import handlers
        results.add_pass("handlers module")
    except Exception as e:
        results.add_fail("handlers", e)
    
    try:
        import commands_admin
        results.add_pass("commands_admin module")
    except Exception as e:
        results.add_fail("commands_admin", e)
    
    try:
        import commands_stats
        results.add_pass("commands_stats module")
    except Exception as e:
        results.add_fail("commands_stats", e)
    
    try:
        import commands_gameplay
        results.add_pass("commands_gameplay module")
    except Exception as e:
        results.add_fail("commands_gameplay", e)
    
    return results

async def test_game_logic():
    """Test game logic functions"""
    results = TestResults()
    print("\n🎲 GAME LOGIC TESTS")
    print("="*50)
    
    try:
        from storage import load_scores, save_scores
        from models import ensure_user_struct, update_elo
        from utils import format_winrate, msg_vittoria, msg_streak, msg_sfiga
        
        # Test user creation
        scores = {}
        ensure_user_struct(scores, "test1", "TestUser1")
        assert "test1" in scores
        results.add_pass("User struct creation")
        
        # Test ELO
        scores["test2"] = {"name": "Player2", "elo": 1000}
        ensure_user_struct(scores, "test2", "Player2")
        gain, loss = update_elo("test1", "test2", scores)
        assert gain > 0 and loss < 0
        results.add_pass("ELO calculation")
        
        # Test formatting
        assert format_winrate(5, 10) == "50.00%"
        results.add_pass("Winrate formatting")
        
        # Test messages
        assert "JACKPOT" in msg_vittoria("Test", True)
        results.add_pass("Victory message")
        
        assert "DOPPIA" in msg_streak("Test", 2)
        results.add_pass("Streak message")
        
        assert msg_sfiga("Test", 5) == ""
        results.add_pass("Sfiga message")
        
        # Save and load
        save_scores(scores)
        loaded = load_scores()
        assert "test1" in loaded
        results.add_pass("Save/load scores")

        # test duel turn helper alternation and win detection
        from commands_gameplay import handle_duel_turn
        import game_state
        # create a dummy duel
        chat = 42
        p1, p2 = "a", "b"
        game_state.ACTIVE_DUELS[chat] = {
            "p1_id": p1,
            "p2_id": p2,
            "p1_name": "P1",
            "p2_name": "P2",
            "current_turn": p1,
            "score": {p1: 0, p2: 0},
        }
        # p1 loses first round (turn passes to p2)
        res = handle_duel_turn(chat, p1, "P1", scores, won=False)
        assert "perde il round" in res
        assert game_state.ACTIVE_DUELS[chat]["current_turn"] == p2
        # simulate a full duel with p2 winning each of their turns
        res = handle_duel_turn(chat, p2, "P2", scores, won=True)  # 1-0
        # p1's turn, lose to pass back
        res = handle_duel_turn(chat, p1, "P1", scores, won=False)
        res = handle_duel_turn(chat, p2, "P2", scores, won=True)  # 2-0
        res = handle_duel_turn(chat, p1, "P1", scores, won=False)
        res = handle_duel_turn(chat, p2, "P2", scores, won=True)  # 3-0, duel should end
        assert "DUELLO FINITO" in res
        results.add_pass("Duel turn helper")
    except Exception as e:
        results.add_fail("Game logic", e)
    
    return results

async def test_commands():
    """Test all commands execute"""
    results = TestResults()
    print("\n📋 COMMAND TESTS")
    print("="*50)
    
    # Setup mocks
    mock_update = MagicMock()
    mock_update.message = MagicMock()
    mock_update.message.from_user.id = 1234567890
    mock_update.message.from_user.first_name = "TestUser"
    mock_update.message.chat_id = 999
    mock_update.message.reply_text = AsyncMock()
    mock_update.message.reply_to_message = None
    mock_update.message.message_id = 100
    
    mock_context = MagicMock()
    mock_context.args = []
    mock_context.bot = MagicMock()
    
    # Import commands
    try:
        from commands_stats import (
            score_command, top_command, topstreak_command, topsfiga_command,
            topcombo_command, topwinrate_command, topspeed_command,
            topduelli_command, storicosfide_command, tope_command
        )
        from commands_gameplay import (
            sfida_command, espansione_command, benedici_command,
            maledici_command, invoca_command, sbusta_command, help_command,
            bestemmia_command
        )
        from commands_admin import helpadmin_command, debug_command, highlights_command
        
        stats_cmds = [
            ("score", score_command),
            ("top", top_command),
            ("topstreak", topstreak_command),
            ("topsfiga", topsfiga_command),
            ("topcombo", topcombo_command),
            ("topwinrate", topwinrate_command),
            ("topspeed", topspeed_command),
            ("tope", tope_command),
            ("topduelli", topduelli_command),
            ("storicosfide", storicosfide_command),
        ]
        
        gameplay_cmds = [
            ("help", help_command),
            ("sbusta", sbusta_command),
            ("benedici", benedici_command),
            ("maledici", maledici_command),
            ("invoca", invoca_command),
            ("bestemmia", bestemmia_command),
        ]
        
        admin_cmds = [
            ("helpadmin", helpadmin_command),
            ("debug", debug_command),
        ]
        
        # include easter egg and lottery commands
        from commands_easter_eggs import slot_command, sfidabot_command
        from commands_minigames import lotteria_command

        stats_cmds.extend([
            ("lotteria", lotteria_command),
        ])
        gameplay_cmds.extend([
            ("slot", slot_command),
            ("sfidabot", sfidabot_command),
        ])
        
        print("\n📊 Stats Commands:")
        for cmd_name, cmd_func in stats_cmds:
            try:
                mock_update.message.reply_text.reset_mock()
                await cmd_func(mock_update, mock_context)
                results.add_pass(f"/{cmd_name}")
            except Exception as e:
                results.add_fail(f"/{cmd_name}", e)

        # test lottery jackpot persistence by calling twice
        mock_update.message.reply_text.reset_mock()
        await lotteria_command(mock_update, mock_context)
        mock_update.message.reply_text.reset_mock()
        await lotteria_command(mock_update, mock_context)
        # after second call file should contain _jackpot key
        import json
        with open('scores.json','r',encoding='utf-8') as f:
            data = json.load(f)
        assert "_jackpot" in data
        results.add_pass("lottery jackpot persisted")
        
        print("\n⚔️  Gameplay Commands:")
        for cmd_name, cmd_func in gameplay_cmds:
            try:
                mock_update.message.reply_text.reset_mock()
                await cmd_func(mock_update, mock_context)
                results.add_pass(f"/{cmd_name}")
            except Exception as e:
                results.add_fail(f"/{cmd_name}", e)
        # check that help command now mentions /bestemmia
        mock_update.message.reply_text.reset_mock()
        await help_command(mock_update, mock_context)
        help_text = mock_update.message.reply_text.call_args[0][0]
        assert "/bestemmia" in help_text
        results.add_pass("help includes bestemmia")
        
        print("\n👑 Admin Commands:")
        for cmd_name, cmd_func in admin_cmds:
            try:
                mock_update.message.reply_text.reset_mock()
                await cmd_func(mock_update, mock_context)
                results.add_pass(f"/{cmd_name}")
            except Exception as e:
                results.add_fail(f"/{cmd_name}", e)

        # custom tests for bestemmia restrictions
        from storage import load_scores, save_scores
        from models import ensure_user_struct
        uid = str(mock_update.message.from_user.id)
        scores = load_scores()
        ensure_user_struct(scores, uid, mock_update.message.from_user.first_name)
        scores[uid]["sfiga"] = 49
        scores[uid]["last_bestemmia_sfiga"] = 0
        save_scores(scores)

        mock_update.message.reply_text.reset_mock()
        await bestemmia_command(mock_update, mock_context)
        assert "Hai bisogno di almeno 50" in mock_update.message.reply_text.call_args[0][0]
        scores = load_scores()
        assert "bestemmia" not in scores[uid].get("achievements", [])
        results.add_pass("bestemmia blocked under threshold")

        scores[uid]["sfiga"] = 50
        save_scores(scores)
        mock_update.message.reply_text.reset_mock()
        await bestemmia_command(mock_update, mock_context)
        # ensure the vent message was sent (contains an emoji or strong phrase)
        resp_text = mock_update.message.reply_text.call_args[0][0]
        assert "🔥" in resp_text
        scores = load_scores()
        assert "bestemmia" in scores[uid].get("achievements", [])
        assert scores[uid]["last_bestemmia_sfiga"] == 50
        results.add_pass("bestemmia allowed and achievement unlocked")

        scores[uid]["sfiga"] = 90
        save_scores(scores)
        mock_update.message.reply_text.reset_mock()
        await bestemmia_command(mock_update, mock_context)
        assert "ancora" in mock_update.message.reply_text.call_args[0][0]
        results.add_pass("bestemmia cooldown check")

        scores[uid]["sfiga"] = 100
        save_scores(scores)
        mock_update.message.reply_text.reset_mock()
        await bestemmia_command(mock_update, mock_context)
        scores = load_scores()
        assert scores[uid]["last_bestemmia_sfiga"] == 100
        results.add_pass("bestemmia reuse after enough sfiga")

        # highlights command test
        from storage import load_scores
        from datetime import datetime, timezone, timedelta
        import json, os

        # ensure yesterday snapshot exists with lower points
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        if not os.path.exists("leaderboard_snapshots"):
            os.makedirs("leaderboard_snapshots")
        scores = load_scores()
        scores[uid]["points"] = 10
        save_scores(scores)
        with open(f"leaderboard_snapshots/{yesterday}_snapshot.json", "w", encoding="utf-8") as f:
            json.dump({"date": yesterday, "top_10": [{"user_id": uid, "name": "TestUser", "points": 10}]}, f)

        # bump points to trigger a mover
        scores[uid]["points"] = 100
        save_scores(scores)
        mock_update.message.reply_text.reset_mock()
        await highlights_command(mock_update, mock_context)
        assert "HIGHLIGHTS" in mock_update.message.reply_text.call_args[0][0]
        assert "TOP 10" in mock_update.message.reply_text.call_args[0][0]
        results.add_pass("highlights command")
    
    except Exception as e:
        results.add_fail("Command import", e)
    
    return results

async def test_dice_handler():
    """Test dice handler"""
    results = TestResults()
    print("\n🎲 DICE HANDLER TESTS")
    print("="*50)
    
    try:
        from handlers import handle_dice
        # ensure debug mode is off so non-admin rolls are allowed
        import game_state
        game_state.DEBUG_MODE = False
        
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.from_user.id = 12345
        mock_update.message.from_user.first_name = "Roller"
        mock_update.message.from_user.is_bot = False
        mock_update.message.chat_id = 888
        mock_update.message.reply_text = AsyncMock()
        mock_update.message.message_id = 200
        mock_update.message.edit_date = None
        mock_update.message.forward_from = None
        mock_update.message.forward_from_chat = None
        mock_update.message.via_bot = None
        
        mock_context = MagicMock()
        mock_context.bot = MagicMock()
        
        # Test with winning roll
        dice_obj = MagicMock()
        dice_obj.emoji = "🎰"
        dice_obj.value = 22  # WIN
        mock_update.message.dice = dice_obj
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            await handle_dice(mock_update, mock_context)
        # debug: print stored score after win
        from storage import load_scores
        print("[dice test] post-win entry:", load_scores().get(str(mock_update.message.from_user.id)))
        results.add_pass("Winning roll (22)")
        
        # Test with losing roll
        mock_update.message.dice.value = 5  # LOSE
        mock_update.message.reply_text.reset_mock()

        with patch('asyncio.sleep', new_callable=AsyncMock):
            await handle_dice(mock_update, mock_context)

        print("[dice test] post-lose entry:", load_scores().get(str(mock_update.message.from_user.id)))
        results.add_pass("Losing roll (5)")
        
        # Test with jackpot
        mock_update.message.dice.value = 64  # JACKPOT
        mock_update.message.reply_text.reset_mock()

        with patch('asyncio.sleep', new_callable=AsyncMock):
            await handle_dice(mock_update, mock_context)

        print("[dice test] post-jackpot entry:", load_scores().get(str(mock_update.message.from_user.id)))
        results.add_pass("Jackpot roll (64)")

        # ensure bot originates dice are ignored
        mock_update.message.from_user.is_bot = True
        mock_update.message.dice.value = 22
        mock_update.message.reply_text.reset_mock()
        with patch('asyncio.sleep', new_callable=AsyncMock):
            await handle_dice(mock_update, mock_context)
        print("[dice test] post-bot-ignore entry:", load_scores().get(str(mock_update.message.from_user.id)))
        results.add_pass("Bot dice ignored")

        # perform two consecutive rolls and check speed recorded
        # first roll already done in previous tests, simulate another
        mock_update.message.from_user.is_bot = False
        mock_update.message.dice.value = 12
        with patch('asyncio.sleep', new_callable=AsyncMock):
            await handle_dice(mock_update, mock_context)
        scores = load_scores()
        uid = str(mock_update.message.from_user.id)
        assert scores[uid].get("best_speed", 0.0) > 0
        results.add_pass("Speed record updated")
        
    except Exception as e:
        results.add_fail("Dice handler", e)
        import traceback
        traceback.print_exc()
    
    return results
async def main():
    print("\n" + "="*50)
    print("🧪 SLOTBOT COMPREHENSIVE TEST SUITE")
    print("="*50)
    
    all_results = TestResults()
    
    # Run test groups
    import_results = await test_imports()
    logic_results = await test_game_logic()
    command_results = await test_commands()
    dice_results = await test_dice_handler()
    
    # Combine results
    all_results.passed = (import_results.passed + logic_results.passed + 
                          command_results.passed + dice_results.passed)
    all_results.failed = (import_results.failed + logic_results.failed + 
                          command_results.failed + dice_results.failed)
    all_results.warnings = (import_results.warnings + logic_results.warnings + 
                            command_results.warnings + dice_results.warnings)
    all_results.errors = (import_results.errors + logic_results.errors + 
                          command_results.errors + dice_results.errors)
    
    # Print summary
    success = all_results.summary()
    
    if success:
        print("✅ ALL TESTS PASSED! Bot is ready to deploy.\n")
        return 0
    else:
        print(f"❌ {all_results.failed} tests failed. Fix errors before deploying.\n")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
