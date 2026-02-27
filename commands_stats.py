"""
Stats and leaderboard commands
"""
from telegram import Update
from telegram.ext import ContextTypes
from storage import load_scores, load_duels, load_users
from utils import format_winrate
from models import get_achievements_display


async def score_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's personal stats"""
    user = update.message.from_user
    user_id = str(user.id)
    nome = user.first_name

    scores = load_scores()

    if user_id not in scores:
        await update.message.reply_text(f"{nome}, non hai ancora nessuna statistica. 🎰")
        return

    d = scores[user_id]
    total_slots = d.get("total_slots", 0)
    total_wins = d.get("total_wins", 0)
    winrate = format_winrate(total_wins, total_slots)
    best_speed = d.get("best_speed", 0.0)

    msg = (
        f"📊 Statistiche di {d['name']}:\n"
        f"• ELO: {d.get('elo', 1000)}\n"
        f"• Punti totali: {d['points']}\n"
        f"• Slot totali tirate: {total_slots}\n"
        f"• Vittorie totali: {total_wins} ({winrate})\n"
        f"• Streak attuale: {d['streak']}\n"
        f"• Record streak: {d['best_streak']}\n"
        f"• Skill issue attuale: {d['sfiga']}\n"
        f"• Record skill issue: {d['best_sfiga']}\n"
        f"• Doppie: {d.get('double', 0)} — Triple: {d.get('triple', 0)} — Poker: {d.get('quad', 0)} — Cinquine: {d.get('quint', 0)}\n"
        f"• Record velocità: {best_speed:.3f} slot/s\n"
        f"• Duelli: {d.get('duel_wins', 0)} vittorie / {d.get('duel_losses', 0)} sconfitte\n"
        f"• Domini espansi: {d.get('domains_used', 0)}\n"
    )
    
    # Add achievements
    achievements = get_achievements_display(scores, user_id)
    if achievements:
        msg += achievements

    await update.message.reply_text(msg)


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show points leaderboard"""
    scores = load_scores()
    if not scores:
        await update.message.reply_text("Nessun punteggio ancora. Qualcuno tiri una slot! 🎰")
        return

    # Filter out corrupted entries (ensure all values are dicts)
    clean_scores = {k: v for k, v in scores.items() if isinstance(v, dict) and "points" in v}
    if not clean_scores:
        await update.message.reply_text("Nessun punteggio valido. Qualcuno tiri una slot! 🎰")
        return

    sorted_players = sorted(clean_scores.items(), key=lambda x: x[1]["points"], reverse=True)

    lines = ["🏆 *CLASSIFICA PUNTI*"]
    for i, (_, d) in enumerate(sorted_players[:10], start=1):
        lines.append(f"{i}. {d['name']} — {d['points']} punti")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def topstreak_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show streak leaderboard"""
    scores = load_scores()
    if not scores:
        await update.message.reply_text("Nessuna streak registrata.")
        return

    # Filter out corrupted entries
    clean_scores = {k: v for k, v in scores.items() if isinstance(v, dict) and "best_streak" in v}
    if not clean_scores:
        await update.message.reply_text("Nessuna streak registrata.")
        return

    sorted_players = sorted(clean_scores.items(), key=lambda x: x[1]["best_streak"], reverse=True)

    lines = ["🔥 *CLASSIFICA STREAK*"]
    for i, (_, d) in enumerate(sorted_players[:10], start=1):
        lines.append(f"{i}. {d['name']} — {d['best_streak']} di fila")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def topsfiga_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show skill issue leaderboard"""
    scores = load_scores()
    if not scores:
        await update.message.reply_text("Nessuna skill issue registrata.")
        return

    # Filter out corrupted entries
    clean_scores = {k: v for k, v in scores.items() if isinstance(v, dict) and "best_sfiga" in v}
    if not clean_scores:
        await update.message.reply_text("Nessun sfiga registrata.")
        return

    sorted_players = sorted(clean_scores.items(), key=lambda x: x[1]["best_sfiga"], reverse=True)

    lines = ["💀 *CLASSIFICA DELLA SKILL ISSUE*"]
    for i, (_, d) in enumerate(sorted_players[:10], start=1):
        lines.append(f"{i}. {d['name']} — {d['best_sfiga']} fallimenti consecutivi")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def topcombo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show combo leaderboard"""
    scores = load_scores()
    if not scores:
        return await update.message.reply_text("Nessuna combo registrata.")

    players = []
    for _, d in scores.items():
        total_combo = d.get("double", 0) + d.get("triple", 0) + d.get("quad", 0) + d.get("quint", 0)
        if total_combo > 0:
            players.append(
                (
                    d["name"],
                    d.get("double", 0),
                    d.get("triple", 0),
                    d.get("quad", 0),
                    d.get("quint", 0),
                    total_combo,
                )
            )

    if not players:
        return await update.message.reply_text("Nessuna combo registrata.")

    players.sort(key=lambda x: x[5], reverse=True)

    lines = ["🎯 *CLASSIFICA COMBO* (doppie/triple/poker/cinquine)"]
    for i, (name, d2, t3, q4, q5, tot) in enumerate(players[:10], start=1):
        lines.append(f"{i}. {name} — {tot} combo (2x:{d2}, 3x:{t3}, 4x:{q4}, 5x:{q5})")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def topwinrate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show winrate leaderboard (min 10 slots)"""
    scores = load_scores()
    if not scores:
        return await update.message.reply_text("Nessuna statistica ancora.")

    players = []
    for _, d in scores.items():
        total_slots = d.get("total_slots", 0)
        total_wins = d.get("total_wins", 0)
        if total_slots >= 10:
            wr = total_wins / total_slots if total_slots > 0 else 0
            players.append((d["name"], wr, total_slots))

    if not players:
        return await update.message.reply_text("Nessuno ha ancora abbastanza slot per una classifica seria (minimo 10).")

    players.sort(key=lambda x: x[1], reverse=True)

    lines = ["📈 *CLASSIFICA WINRATE* (min 10 slot)"]
    for i, (name, wr, ts) in enumerate(players[:10], start=1):
        lines.append(f"{i}. {name} — {wr*100:.2f}% su {ts} slot")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def topspeed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show speed leaderboard"""
    scores = load_scores()
    if not scores:
        return await update.message.reply_text("Nessuna slot ancora, nessuna velocità da misurare.")

    players = []
    for _, d in scores.items():
        bs = d.get("best_speed", 0.0)
        if bs > 0:
            players.append((d["name"], bs))

    if not players:
        return await update.message.reply_text("Nessun record di velocità registrato.")

    players.sort(key=lambda x: x[1], reverse=True)

    lines = ["⚡ *CLASSIFICA VELOCITÀ SLOT* (slot/s)"]
    for i, (name, bs) in enumerate(players[:10], start=1):
        lines.append(f"{i}. {name} — {bs:.3f} slot/s")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def tope_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show ELO leaderboard"""
    scores = load_scores()
    if not scores:
        return await update.message.reply_text("Nessun ELO registrato.")

    players = []
    for _, d in scores.items():
        players.append((d["name"], d.get("elo", 1000)))

    players.sort(key=lambda x: x[1], reverse=True)

    lines = ["🏅 *CLASSIFICA ELO*"]
    for i, (name, elo) in enumerate(players[:10], start=1):
        lines.append(f"{i}. {name} — {elo}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def topduelli_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show duel leaderboard"""
    scores = load_scores()
    if not scores:
        return await update.message.reply_text("Nessun duello registrato.")

    players = []
    for _, d in scores.items():
        wins = d.get("duel_wins", 0)
        losses = d.get("duel_losses", 0)
        if wins + losses > 0:
            players.append((d["name"], wins, losses))

    if not players:
        return await update.message.reply_text("Nessun duello registrato.")

    players.sort(key=lambda x: x[1], reverse=True)

    lines = ["⚔️ *CLASSIFICA DUELLI*"]
    for i, (name, w, l) in enumerate(players[:10], start=1):
        lines.append(f"{i}. {name} — {w} vittorie / {l} sconfitte")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def storicosfide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show last 10 duels"""
    duels = load_duels()
    if not duels:
        return await update.message.reply_text("Nessuna sfida in archivio.")

    last = duels[-10:]
    lines = ["📜 *STORICO SFIDE* (ultime 10)"]
    for d in reversed(last):
        lines.append(
            f"{d['p1']} vs {d['p2']}: {d['score1']} - {d['score2']} (vincitore: {d['winner']})"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
