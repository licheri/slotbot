import asyncio
import random
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from config import WIN_VALUES, ADMIN_ID, DOMAIN_EXPANSION_DURATION
from storage import load_scores, save_scores, load_users, save_users, load_duels, save_duels
from models import ensure_user_struct
from utils import (
    msg_vittoria, msg_streak, msg_sfiga, 
    is_expansion_active
)
from commands_gameplay import handle_duel_turn
import game_state


async def handle_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main handler for slot dice rolls"""
    if update.message is None or update.message.dice is None:
        return

    chat_id = update.message.chat_id
    user_id_int = update.message.from_user.id

    # >>> DEBUG MODE: only admin can roll
    if game_state.DEBUG_MODE:
        if user_id_int != ADMIN_ID:
            return

    # ignore rolls initiated by other bots (including ourselves) - they should not count
    if getattr(update.message.from_user, "is_bot", False):
        return

    # Check if slot tracking is blocked
    if game_state.SLOT_BLOCKED:
        await update.message.reply_text(
            "⛔ Il tracking delle slot è temporaneamente disattivato dall'amministratore.",
            parse_mode="Markdown"
        )
        return

    dice = update.message.dice
    if dice.emoji != "🎰":
        return

    # ============================================================
    #   FAILSAFE ANTI-CHEAT
    # ============================================================
    if not game_state.DEBUG_MODE:
        # 1) BLOCK FORWARDED MESSAGES
        fwd_user = getattr(update.message, "forward_from", None)
        fwd_chat = getattr(update.message, "forward_from_chat", None)

        if fwd_user or fwd_chat:
            await update.message.reply_text(
                "❌ Non puoi inoltrare una slot. Nice try.",
                parse_mode="Markdown"
            )
            return

        # 2) BLOCK EDITED MESSAGES
        if getattr(update.message, "edit_date", None):
            await update.message.reply_text(
                "❌ Slot modificata? Non funziona così.",
                parse_mode="Markdown"
            )
            return

        # 3) BLOCK MESSAGES VIA BOT
        if getattr(update.message, "via_bot", None):
            await update.message.reply_text(
                "❌ Non puoi usare bot esterni per tirare slot.",
                parse_mode="Markdown"
            )
            return

        # 4) VERIFY AUTHENTIC DICE
        dice_obj = getattr(update.message, "dice", None)
        if dice_obj is None:
            await update.message.reply_text(
                "❌ Questo non è un vero tiro di slot.",
                parse_mode="Markdown"
            )
            return

    # ============================================================
    #   END FAILSAFE
    # ============================================================

    # Check if domain expansion ended
    if chat_id in game_state.EXPANSION_UNTIL:
        if game_state.EXPANSION_UNTIL[chat_id] > 0 and game_state.EXPANSION_UNTIL[chat_id] < datetime.now(timezone.utc).timestamp():
            await update.message.reply_text(
                "🌌 *Il dominio si dissolve.*\n"
                "La realtà torna stabile.",
                parse_mode="Markdown"
            )
            game_state.EXPANSION_UNTIL[chat_id] = 0

    # Measure speed BEFORE sleep
    now_ts = datetime.now(timezone.utc).timestamp()
    
    # Load scores to get last timestamp
    scores = load_scores()
    user_id = str(user_id_int)
    ensure_user_struct(scores, user_id, update.message.from_user.first_name)
    
    last_ts = scores[user_id]["last_slot_ts"]
    scores[user_id]["last_slot_ts"] = now_ts

    # Sleep to not spoil animation
    await asyncio.sleep(1)

    # Now process the roll
    message = update.message
    user = message.from_user
    nome = user.first_name
    chat_id = message.chat_id

    # Update users list
    users = load_users()
    users[user_id] = nome
    save_users(users)

    # Reload scores (in case they were updated during sleep)
    scores = load_scores()
    ensure_user_struct(scores, user_id, nome)

    # we must make sure the timestamp we calculated before the sleep is
    # preserved, otherwise the field would revert to its previous value and
    # the speed check would never see a delta. reapply it here.
    scores[user_id]["last_slot_ts"] = now_ts

    jackpot = (dice.value == 64)

    # -------------------------------------------------------
    #   DOMAIN EXPANSION REROLL
    # -------------------------------------------------------
    if is_expansion_active(chat_id):
        if scores[user_id]["last_was_win"] and dice.value not in WIN_VALUES:
            if random.random() < 0.33:  # Hakari probability
                try:
                    await context.bot.delete_message(
                        chat_id=chat_id,
                        message_id=message.message_id
                    )
                except:
                    pass

                await update.message.reply_text(
                    "🌌 *IDLE DEATH GAMBLE*\n"
                    "La tua sconfitta è stata *cancellata*.",
                    parse_mode="Markdown"
                )
                return

    # -------------------------------------------------------
    #   GENERAL TRACKING
    # -------------------------------------------------------
    scores[user_id]["total_slots"] += 1

    speed_msg = ""
    if last_ts > 0:  # Only track speed if not first roll
        delta = now_ts - last_ts
        if delta > 0:  # we only care about positive intervals
            speed = 1.0 / delta
            best_speed = scores[user_id].get("best_speed", 0.0)
            if best_speed == 0.0 or speed > best_speed:  # First time or new record
                scores[user_id]["best_speed"] = speed
                speed_msg = f"\n⚡ Nuovo record personale di velocità per {nome}: {speed:.3f} slot/s"

    msg = ""

    # -------------------------------------------------------
    #   WIN
    # -------------------------------------------------------
    if dice.value in WIN_VALUES:
        scores[user_id]["last_was_win"] = True

        scores[user_id]["sfiga"] = 0
        scores[user_id]["streak"] += 1
        streak = scores[user_id]["streak"]

        if streak > scores[user_id]["best_streak"]:
            scores[user_id]["best_streak"] = streak

        scores[user_id]["total_wins"] += 1

        if streak == 2:
            scores[user_id]["double"] += 1
        elif streak == 3:
            scores[user_id]["triple"] += 1
            # Triple notification - can activate domain
            await message.reply_text(
                f"🎲 *JACKPOT PROBABILITY RISING*\n"
                f"{nome} ha ottenuto una *TRIPLA*.\n"
                f"L'energia del dominio vibra attorno a lui…\n"
                f"Può attivare l'ESPANSIONE entro i prossimi *10 messaggi*.",
                parse_mode="Markdown"
            )

            scores[user_id]["last_triple_msg_id"] = message.message_id

        elif streak == 4:
            scores[user_id]["quad"] += 1
        elif streak == 5:
            scores[user_id]["quint"] += 1

        # Point calculation
        if jackpot:
            scores[user_id]["points"] += 2
        else:
            scores[user_id]["points"] += 1

        if streak == 2:
            scores[user_id]["points"] += 1
        elif streak == 3:
            scores[user_id]["points"] += 1
        elif streak == 4:
            scores[user_id]["points"] += 2
        elif streak == 5:
            scores[user_id]["points"] += 3

        if is_expansion_active(chat_id):
            scores[user_id]["points"] += 1
            msg += "🌌 *ESPANSIONE DEL DOMINIO ATTIVA*\n"

        msg += msg_vittoria(nome, jackpot)
        streak_msg = msg_streak(nome, streak)
        if streak_msg:
            msg += f"\n{streak_msg}"

        # handle duel turn with a win flag
        duel_msg = handle_duel_turn(chat_id, user_id, nome, scores, True)
        if duel_msg:
            msg += f"{duel_msg}"

    # -------------------------------------------------------
    #   LOSS
    # -------------------------------------------------------
    else:
        scores[user_id]["last_was_win"] = False

        scores[user_id]["streak"] = 0
        scores[user_id]["sfiga"] += 1
        sfiga = scores[user_id]["sfiga"]

        if sfiga > scores[user_id]["best_sfiga"]:
            scores[user_id]["best_sfiga"] = sfiga

        msg = msg_sfiga(nome, sfiga)

        # handle duel turn on a losing roll (turn still passes)
        duel_msg = handle_duel_turn(chat_id, user_id, nome, scores, False)
        if duel_msg:
            msg += f"{duel_msg}"

    if speed_msg:
        if msg:
            msg += speed_msg
        else:
            msg = speed_msg.lstrip()

    if msg:
        await message.reply_text(msg, parse_mode="Markdown")
    # debug: log what we're about to save (especially during tests)
    try:
        print(f"[handle_dice] saving scores keys: {list(scores.keys())}")
    except Exception:
        pass
    save_scores(scores)
