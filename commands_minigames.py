"""
Mini-game commands - tarocchi, lotteria, evento
"""
import random
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from storage import load_scores, save_scores
from models import ensure_user_struct, unlock_achievement


# Tarocchi data
TAROCCHI = [
    ("0 - Il Matto", "Inizio di un nuovo ciclo... o fine di uno vecchio? 🌀"),
    ("I - L'Illusionista", "La tua velocità ti farà vincere oggi. ⚡"),
    ("II - La Sacerdotessa", "C'è un segreto nascosto nei tuoi dati... 🔮"),
    ("III - L'Imperatrice", "Il tuo prossimo slot sarà MONUMENTALE. 👑"),
    ("IV - L'Imperatore", "Domina il tavolo oggi, il potere è tuo. 💪"),
    ("V - Il Gerofante", "La saggezza ti guiderà a scelte corrette. 🧙"),
    ("VI - Gli Innamorati", "Una connessione speciale ti porta fortuna. 💞"),
    ("VII - Il Carro", "Vittoria in vista! La rotta è giusta. 🏆"),
    ("VIII - La Forza", "Il tuo coraggio sarà ricompensato. 🦁"),
    ("IX - L'Eremita", "La solitudine del pensiero porterà rivelazioni. 🕯️"),
    ("X - La Ruota di Fortuna", "La sorte gira a tuo favore. 🎡"),
    ("XI - La Giustizia", "Azioni equilibrate portano risultati equilibrati. ⚖️"),
    ("XII - L'Impiccato", "A volte bisogna cambiare prospettiva. 🪢"),
    ("XIII - La Morte", "Fine di uno era, inizio di un'altra. 🦴"),
    ("XIV - La Temperanza", "Moderazione e pazienza oggi pagheranno. 🏺"),
    ("XV - Il Diavolo", "Attenzione! Pero le tentazioni portano grandi vincite. 😈"),
    ("XVI - La Torre", "Cambiamento improvviso... buono o cattivo? ⚡"),
    ("XVII - La Stella", "La tua stella brilla luminosa stasera. ✨"),
    ("XVIII - La Luna", "Verità nascoste emergono nei riflessi. 🌙"),
    ("XIX - Il Sole", "Una giornata SPLENDENTE ti aspetta. ☀️"),
    ("XX - Il Giudizio", "È tempo di rinascita e trasformazione. 📯"),
    ("XXI - Il Mondo", "Completamento e realizzazione di cicli. 🌍"),
]


# Random events
EVENTOS = [
    {
        "name": "Duello Rapido",
        "desc": "Tira 3 slot - più vittorie = più punti bonus!",
        "emoji": "⚡",
        "rewards": [10, 20, 30]  # per 1, 2, 3 vittorie
    },
    {
        "name": "Sfida della Velocità",
        "desc": "Hai 10 secondi - quante slot tiri? +1 punto per ogni tiro!",
        "emoji": "🏃",
        "rewards": "per_tiro"
    },
    {
        "name": "Combinazione Lucky",
        "desc": "Scegli un numero da 1 a 64. Se tiri dentro 3 slot, vinci 50 punti!",
        "emoji": "🎰",
        "rewards": 50
    },
    {
        "name": "Roulette Russa",
        "desc": "Tira 1 slot. Se vinci, triplicati i tuoi punti giornalieri! Se perdi... -10.",
        "emoji": "🎲",
        "rewards": "multiplier"
    },
    {
        "name": "Memoria Spaziale",
        "desc": "Indovina 3 numeri random da 1 a 64. Ogni indovinello = +5 punti.",
        "emoji": "🧠",
        "rewards": "per_guess"
    },
]


async def tarocchi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Daily tarot reading"""
    message = update.message
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    
    scores = load_scores()
    ensure_user_struct(scores, user_id, user_name)
    
    # Check one-per-day cooldown
    now_ts = datetime.now(timezone.utc).timestamp()
    last_tarocchi = scores[user_id].get("last_tarocchi_ts", 0)
    
    if last_tarocchi > 0 and now_ts - last_tarocchi < 86400:
        hours_remaining = int((86400 - (now_ts - last_tarocchi)) / 3600)
        return await message.reply_text(
            f"🔮 Le carte sono già state rivelate!\n"
            f"Torneranno disponibili tra circa {hours_remaining} ore.",
            parse_mode="Markdown"
        )
    
    # Update last tarocchi timestamp
    scores[user_id]["last_tarocchi_ts"] = now_ts
    save_scores(scores)
    
    # Draw card
    card = random.choice(TAROCCHI)
    
    msg = (
        f"🔮 *LETTURA DEI TAROCCHI* 🔮\n\n"
        f"*{card[0]}*\n\n"
        f"_{card[1]}_\n\n"
        f"✨ La carta ha parlato, {user_name}. Il destino è nelle tue mani."
    )
    
    unlock_achievement(scores, user_id, "tarot_reader")
    save_scores(scores)
    
    await message.reply_text(msg, parse_mode="Markdown")


async def lotteria_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Weekly lottery - only once per week per player"""
    message = update.message
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    
    scores = load_scores()
    ensure_user_struct(scores, user_id, user_name)
    
    # Check one-per-week cooldown (7 giorni)
    now_ts = datetime.now(timezone.utc).timestamp()
    last_lotteria = scores[user_id].get("last_lotteria_ts", 0)
    
    if last_lotteria > 0 and now_ts - last_lotteria < 604800:
        days_remaining = int((604800 - (now_ts - last_lotteria)) / 86400)
        return await message.reply_text(
            f"🎰 Hai già partecipato a questa settimana!\n"
            f"La prossima estrazione sarà tra circa {days_remaining} giorni.",
            parse_mode="Markdown"
        )
    
    # Update last lotteria timestamp
    scores[user_id]["last_lotteria_ts"] = now_ts

    # Read current jackpot (stored in scores under key _jackpot)
    jackpot = scores.get("_jackpot", 0)
    
    # Draw lucky number
    lucky_num = random.randint(1, 100)
    user_num = random.randint(1, 100)
    
    # 20% chance to win
    won = user_num == lucky_num or random.random() < 0.20
    
    if won:
        prize = jackpot + random.randint(100, 500)
        scores[user_id]["points"] += prize
        jackpot = 50  # Reset jackpot
        
        msg = (
            f"🎰 *LOTTERIA SETTIMANALE* 🎰\n\n"
            f"🍀 *VINCITA!*\n"
            f"Il numero fortunato era: *{lucky_num}*\n"
            f"Il tuo numero era: *{user_num}*\n\n"
            f"🏆 Hai vinto: *{prize} punti*!\n"
            f"Congratulazioni {user_name}! La fortuna è dalla tua parte!"
        )
        unlock_achievement(scores, user_id, "lottery_winner")
    else:
        jackpot += 50  # Add to jackpot for next winner
        
        msg = (
            f"🎰 *LOTTERIA SETTIMANALE* 🎰\n\n"
            f"❌ *SFORTUNATO*\n"
            f"Il numero fortunato era: *{lucky_num}*\n"
            f"Il tuo numero era: *{user_num}*\n\n"
            f"Il jackpot salirà a: *{jackpot} punti* per il prossimo vincitore!\n"
            f"Riprova il prossimo giovedì, {user_name}."
        )

    # Save both scores and updated jackpot
    scores["_jackpot"] = jackpot
    save_scores(scores)
    
    await message.reply_text(msg, parse_mode="Markdown")


async def evento_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Random mini-event - Sunday only, once per week"""
    message = update.message
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    
    scores = load_scores()
    ensure_user_struct(scores, user_id, user_name)
    
    # Check if it's Sunday (weekday 6)
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    if now.weekday() != 6:  # 0=Monday, 6=Sunday
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        return await message.reply_text(
            f"⚡ L'evento è solo di domenica!\n"
            f"Torna tra {days_until_sunday} giorni per partecipare.",
            parse_mode="Markdown"
        )
    
    # Check one-per-week cooldown
    now_ts = datetime.now(timezone.utc).timestamp()
    last_evento = scores[user_id].get("last_evento_ts", 0)
    
    if last_evento > 0 and now_ts - last_evento < 604800:  # 604800 = 7 giorni
        days_remaining = int((604800 - (now_ts - last_evento)) / 86400)
        return await message.reply_text(
            f"⚡ Hai già partecipato all'evento questa settimana!\n"
            f"Il prossimo sarà disponibile tra circa {days_remaining} giorni.",
            parse_mode="Markdown"
        )
    
    # Update last evento timestamp
    scores[user_id]["last_evento_ts"] = now_ts
    
    # Pick random evento
    event = random.choice(EVENTOS)
    
    # Simulate event outcome (simplified version)
    if event["name"] == "Duello Rapido":
        rolls = [random.randint(1, 64) for _ in range(3)]
        wins = sum(1 for r in rolls if r >= 43)
        reward = event["rewards"][wins]
        scores[user_id]["points"] += reward
        msg = (
            f"{event['emoji']} *{event['name'].upper()}* {event['emoji']}\n\n"
            f"{event['desc']}\n\n"
            f"Risultato: {wins} vittorie su 3!\n"
            f"🏆 Hai vinto *{reward} punti*!"
        )
    elif event["name"] == "Combinazione Lucky":
        target_num = random.randint(1, 64)
        hits = 0
        for _ in range(3):
            roll = random.randint(1, 64)
            if roll == target_num:
                hits += 1
        if hits > 0:
            reward = event["rewards"]
            scores[user_id]["points"] += reward
            msg = (
                f"{event['emoji']} *{event['name'].upper()}* {event['emoji']}\n\n"
                f"{event['desc']}\n\n"
                f"Numero target: *{target_num}*\n"
                f"Hai colpito: *{hits}* volte!\n"
                f"🏆 Hai vinto *{reward} punti*!"
            )
        else:
            msg = (
                f"{event['emoji']} *{event['name'].upper()}* {event['emoji']}\n\n"
                f"{event['desc']}\n\n"
                f"Numero target: *{target_num}*\n"
                f"❌ Peccato, non hai colpito nessuna volta."
            )
    elif event["name"] == "Sfida della Velocità":
        # simulate how many slots the user would manage in 10 seconds
        rolls = random.randint(0, 20)  # arbitrary range
        scores[user_id]["points"] += rolls
        msg = (
            f"{event['emoji']} *{event['name'].upper()}* {event['emoji']}\n\n"
            f"{event['desc']}\n\n"
            f"Hai fatto *{rolls}* slot in 10 secondi!\n"
            f"🏆 Hai guadagnato *{rolls} punti*!"
        )
    elif event["name"] == "Roulette Russa":
        roll = random.randint(1, 64)
        if roll >= 43:
            multiplier = 3
            old_points = scores[user_id]["points"]
            scores[user_id]["points"] *= multiplier
            msg = (
                f"{event['emoji']} *{event['name'].upper()}* {event['emoji']}\n\n"
                f"{event['desc']}\n\n"
                f"🎲 Hai tirato un numero vincente!\n"
                f"💰 I tuoi punti sono passati da {old_points} a {scores[user_id]['points']}!"
            )
        else:
            scores[user_id]["points"] -= 10
            msg = (
                f"{event['emoji']} *{event['name'].upper()}* {event['emoji']}\n\n"
                f"{event['desc']}\n\n"
                f"💥 Hai perso la roulette!\n"
                f"-10 punti per questa volta..."
            )
    else:
        # Generic event
        reward = random.randint(20, 50)
        scores[user_id]["points"] += reward
        msg = (
            f"{event['emoji']} *{event['name'].upper()}* {event['emoji']}\n\n"
            f"{event['desc']}\n\n"
            f"🏆 Hai vinto *{reward} punti*!"
        )
    
    unlock_achievement(scores, user_id, "event_master")
    save_scores(scores)
    
    await message.reply_text(msg, parse_mode="Markdown")
