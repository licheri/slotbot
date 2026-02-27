"""
Easter egg commands - bot slot rolling and bot duels
"""
import asyncio
import random
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from storage import load_scores, save_scores
from models import ensure_user_struct


async def slot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Easter egg: bot tira slot da solo (1-10 volte, max una volta al giorno)"""
    message = update.message
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    chat_id = message.chat_id

    scores = load_scores()
    ensure_user_struct(scores, user_id, user_name)
    
    # Check one-per-day cooldown
    now_ts = datetime.now(timezone.utc).timestamp()
    last_slot_bot = scores[user_id].get("last_slot_bot_ts", 0)
    
    if last_slot_bot > 0 and now_ts - last_slot_bot < 86400:  # 86400 = 1 giorno
        hours_remaining = int((86400 - (now_ts - last_slot_bot)) / 3600)
        return await message.reply_text(
            f"⏳ Il bot è stanco!\n"
            f"Tornerà tra circa {hours_remaining} ore.",
            parse_mode="Markdown"
        )
    
    # Update last slot bot timestamp
    scores[user_id]["last_slot_bot_ts"] = now_ts
    save_scores(scores)
    
    # Bot rolls 1-10 times
    num_rolls = random.randint(1, 10)
    
    bot_messages = [
        "🤖 *Accendo i circuiti...*",
        "🎰 *MI SENTO FORTUNATO*",
        "🎲 *Ecco a te, mortale!*",
        "✨ *Il fato è dalla mia parte...*",
        "⚡ *Energia quantica attivata!*",
    ]
    
    await message.reply_text(random.choice(bot_messages), parse_mode="Markdown")
    
    # Simulate bot rolls
    wins = 0
    for i in range(num_rolls):
        roll = random.randint(1, 64)
        is_win = roll in [43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64]
        if is_win:
            wins += 1
    
    result_messages = [
        f"🤖 Ho tirato {num_rolls} volte e ho vinto {wins} volte! *Non male, eh?* 🎉",
        f"🎲 Risultato: {wins} vittorie su {num_rolls} tentativi. Sono *inarrestabile*! 💪",
        f"⚡ Statistiche bot: {wins}/{num_rolls} vittorie. Voi umani non potete competere.",
        f"🌟 Eccellente! Ho ottenuto {wins} vittorie in {num_rolls} slot. *Il dominio è mio*! 👑",
    ]
    
    await message.reply_text(random.choice(result_messages), parse_mode="Markdown")


async def sfidabot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Challenge the bot (best of 3, max once per day)"""
    message = update.message
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    chat_id = message.chat_id
    
    scores = load_scores()
    ensure_user_struct(scores, user_id, user_name)
    
    # Check one-per-day cooldown
    now_ts = datetime.now(timezone.utc).timestamp()
    last_duel_bot = scores[user_id].get("last_duel_bot_ts", 0)
    
    if last_duel_bot > 0 and now_ts - last_duel_bot < 86400:
        hours_remaining = int((86400 - (now_ts - last_duel_bot)) / 3600)
        return await message.reply_text(
            f"⏳ Il bot ha bisogno di ricaricarsi!\n"
            f"Sarà disponibile tra circa {hours_remaining} ore.",
            parse_mode="Markdown"
        )
    
    # Update last duel bot timestamp
    scores[user_id]["last_duel_bot_ts"] = now_ts
    save_scores(scores)
    
    # Simulate bot duel
    player_wins = 0
    bot_wins = 0
    
    await message.reply_text(
        f"⚔️ *SFIDA EPICA*\n"
        f"🤖 *Il bot accetta la sfida!*\n"
        f"Primo a 3 vittorie vince...",
        parse_mode="Markdown"
    )
    
    # Simulate rounds
    while player_wins < 3 and bot_wins < 3:
        player_roll = random.randint(1, 64)
        bot_roll = random.randint(1, 64)
        
        player_win = player_roll in [43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64]
        bot_win = bot_roll in [43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64]
        
        if player_win and not bot_win:
            player_wins += 1
            round_msg = f"🎲 *Round {player_wins + bot_wins}*\n{user_name} vince! ({player_wins}-{bot_wins})"
        elif bot_win and not player_win:
            bot_wins += 1
            round_msg = f"🎲 *Round {player_wins + bot_wins}*\n🤖 Il bot vince! ({player_wins}-{bot_wins})"
        else:
            round_msg = f"🎲 *Round {player_wins + bot_wins}*\nPareggio! Rivincita..."
            continue
        
        await message.reply_text(round_msg, parse_mode="Markdown")
        
        # Small delay between rounds for suspense
        await asyncio.sleep(0.5)
    
    # Determine overall winner
    if player_wins == 3:
        win_messages = [
            f"🏆 *HAI VINTO!* 🏆\nCongratulazioni {user_name}! Hai battuto l'IA!\nIl bot ti inchina rispettosamente.",
            f"⚡ *INCREDIBILE!* ⚡\n{user_name} ha superato i limiti della logica quantica!\nIl bot è... impressionato.",
            f"🌟 *LEGGENDARIO!* 🌟\nAncora una volta, l'istinto umano batte la freddezza della macchina!\nVai {user_name}, vai!",
        ]
        scores[user_id]["duel_wins"] += 1
    else:
        win_messages = [
            f"🤖 *IL BOT VINCE!* 🤖\nNon sei abbastanza veloce, {user_name}.\nMeglio fortuna la prossima volta.",
            f"⚙️ *ELIMINATO* ⚙️\nIl bot ha dimostrato la superiorità della macchina.\nRitorna quando sei più forte, {user_name}.",
            f"💻 *PROCESSO COMPLETATO* 💻\nIl bot celebra la vittoria sulla biologia umana.\nRiprova domani, se ne hai il coraggio!",
        ]
        scores[user_id]["duel_losses"] += 1
    
    save_scores(scores)
    await message.reply_text(random.choice(win_messages), parse_mode="Markdown")
