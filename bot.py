import json
import os
import asyncio
from typing import Dict, Any
import random
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")
SCORES_FILE = "scores.json"
USERS_FILE = "users.json"
DUELS_FILE = "duels.json"
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

WIN_VALUES = {1, 22, 43, 64}

# Duelli attivi per chat
ACTIVE_DUELS: Dict[int, Dict[str, Any]] = {}
# Espansione del dominio per chat: chat_id -> timestamp fine
EXPANSION_UNTIL: Dict[int, float] = {}
# Blocco globale dello slot tracking
SLOT_BLOCKED = False


# -------------------------------
#   ADMIN
# -------------------------------
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


async def setpoints_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    if len(context.args) != 2:
        return await update.message.reply_text("Uso: /setpoints <user_id> <punti>")

    target_id = context.args[0]
    try:
        new_points = int(context.args[1])
    except:
        return await update.message.reply_text("I punti devono essere un numero.")

    scores = load_scores()
    if target_id not in scores:
        return await update.message.reply_text("Utente non trovato.")

    scores[target_id]["points"] = new_points
    save_scores(scores)

    await update.message.reply_text(f"Punti aggiornati per {scores[target_id]['name']}: {new_points}")


async def addpoints_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    if len(context.args) != 2:
        return await update.message.reply_text("Uso: /addpoints <user_id> <punti>")

    target_id = context.args[0]
    try:
        add = int(context.args[1])
    except:
        return await update.message.reply_text("I punti devono essere un numero.")

    scores = load_scores()
    if target_id not in scores:
        return await update.message.reply_text("Utente non trovato.")

    scores[target_id]["points"] += add
    save_scores(scores)

    await update.message.reply_text(
        f"Aggiunti {add} punti a {scores[target_id]['name']}. Totale: {scores[target_id]['points']}"
    )


async def setstreak_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    if len(context.args) != 2:
        return await update.message.reply_text("Uso: /setstreak <user_id> <streak>")

    target_id = context.args[0]
    try:
        new_streak = int(context.args[1])
    except:
        return await update.message.reply_text("La streak deve essere un numero.")

    scores = load_scores()
    if target_id not in scores:
        return await update.message.reply_text("Utente non trovato.")

    scores[target_id]["streak"] = new_streak
    if new_streak > scores[target_id]["best_streak"]:
        scores[target_id]["best_streak"] = new_streak

    save_scores(scores)

    await update.message.reply_text(f"Streak aggiornata per {scores[target_id]['name']}: {new_streak}")


async def setsfiga_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    if len(context.args) != 2:
        return await update.message.reply_text("Uso: /setsfiga <user_id> <sfiga>")

    target_id = context.args[0]
    try:
        new_sfiga = int(context.args[1])
    except:
        return await update.message.reply_text("La sfiga deve essere un numero.")

    scores = load_scores()
    if target_id not in scores:
        return await update.message.reply_text("Utente non trovato.")

    scores[target_id]["sfiga"] = new_sfiga
    if new_sfiga > scores[target_id]["best_sfiga"]:
        scores[target_id]["best_sfiga"] = new_sfiga

    save_scores(scores)

    await update.message.reply_text(f"Sfiga aggiornata per {scores[target_id]['name']}: {new_sfiga}")


async def exportjson_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    scores = load_scores()
    text = json.dumps(scores, ensure_ascii=False, indent=2)

    await update.message.reply_text(f"📦 JSON attuale:\n```\n{text}\n```", parse_mode="Markdown")


async def importjson_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    if not update.message.reply_to_message:
        return await update.message.reply_text("Rispondi a un messaggio contenente il JSON.")

    raw = update.message.reply_to_message.text

    try:
        data = json.loads(raw)
    except:
        return await update.message.reply_text("JSON non valido.")

    save_scores(data)
    await update.message.reply_text("✔️ JSON importato correttamente.")

async def blockslot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global SLOT_BLOCKED
    user = update.message.from_user

    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    SLOT_BLOCKED = True

    await update.message.reply_text(
        "⛔ *SLOT TRACKING BLOCCATO*\n"
        "Da questo momento il bot ignorerà *tutte* le slot tirate.\n\n"
        "*DISCLAIMER*: questa funzione è pensata solo per manutenzione o test.\n"
        "Finché il blocco è attivo:\n"
        "• nessuna slot viene registrata\n"
        "• nessuna streak avanza\n"
        "• nessuna sfiga aumenta\n"
        "• nessun duello progredisce\n"
        "• nessun punto viene assegnato",
        parse_mode="Markdown"
    )


async def unblockslot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global SLOT_BLOCKED
    user = update.message.from_user

    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    SLOT_BLOCKED = False

    await update.message.reply_text(
        "✅ *SLOT TRACKING RIATTIVATO*\n"
        "Il bot ora registra di nuovo tutte le slot.",
        parse_mode="Markdown"
    )


# -------------------------------
#   STORAGE
# -------------------------------
def load_scores() -> Dict[str, Any]:
    if not os.path.exists(SCORES_FILE):
        return {}
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_scores(scores: Dict[str, Any]) -> None:
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_duels():
    if not os.path.exists(DUELS_FILE):
        return []
    try:
        with open(DUELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_duels(duels):
    with open(DUELS_FILE, "w", encoding="utf-8") as f:
        json.dump(duels, f, ensure_ascii=False, indent=2)


# -------------------------------
#   USER STRUCT + ELO
# -------------------------------
def ensure_user_struct(scores: Dict[str, Any], user_id: str, nome: str):
    if user_id not in scores:
        scores[user_id] = {
            "name": nome,
            "points": 0,
            "streak": 0,
            "best_streak": 0,
            "sfiga": 0,
            "best_sfiga": 0,
            "total_slots": 0,
            "total_wins": 0,
            "double": 0,
            "triple": 0,
            "quad": 0,
            "quint": 0,
            "duel_wins": 0,
            "duel_losses": 0,
            "elo": 1000,
            "best_speed": 0.0,
            "last_slot_ts": 0.0,
            "last_was_win": False,
        }
    else:
        scores[user_id].setdefault("total_slots", 0)
        scores[user_id].setdefault("total_wins", 0)
        scores[user_id].setdefault("double", 0)
        scores[user_id].setdefault("triple", 0)
        scores[user_id].setdefault("quad", 0)
        scores[user_id].setdefault("quint", 0)
        scores[user_id].setdefault("duel_wins", 0)
        scores[user_id].setdefault("duel_losses", 0)
        scores[user_id].setdefault("elo", 1000)
        scores[user_id].setdefault("best_speed", 0.0)
        scores[user_id].setdefault("last_slot_ts", 0.0)
        scores[user_id].setdefault("last_was_win", False)
        scores[user_id]["name"] = nome


def update_elo(winner_id: str, loser_id: str, scores: Dict[str, Any]) -> (int, int):
    K = 32
    Ra = scores[winner_id]["elo"]
    Rb = scores[loser_id]["elo"]

    Ea = 1 / (1 + 10 ** ((Rb - Ra) / 400))
    Eb = 1 / (1 + 10 ** ((Ra - Rb) / 400))

    new_Ra = int(Ra + K * (1 - Ea))
    new_Rb = int(Rb + K * (0 - Eb))

    scores[winner_id]["elo"] = new_Ra
    scores[loser_id]["elo"] = new_Rb

    return new_Ra - Ra, new_Rb - Rb


# -------------------------------
#   MESSAGGI GOLIARDICI
# -------------------------------
def msg_vittoria(nome: str, jackpot: bool) -> str:
    if jackpot:
        return f"💥 JACKPOT! {nome} no vabbé assurdo!"
    return f"🎉 {nome} ha max slottato!"


def msg_streak(nome: str, streak: int) -> str:
    if streak == 2:
        return f"⚡ {nome} sta volando: *DOPPIA*!"
    if streak == 3:
        return f"🔥🔥 {nome} ha scoperto il seed: *TRIPLA*!"
    if streak == 4:
        return f"🧨 {nome} stai esagerando: *POKER*!"
    if streak == 5:
        return f"👑 *King Slot* {nome}: *CINQUINA*."
    return ""


def msg_sfiga(nome: str, sfiga: int) -> str:
    if sfiga >= 50 and sfiga % 10 == 0:
        return f"💀 {nome} ha le skill issues: {sfiga} slot senza vincere."
    return ""


def format_winrate(total_wins: int, total_slots: int) -> str:
    if total_slots == 0:
        return "0.00%"
    perc = (total_wins / total_slots) * 100
    return f"{perc:.2f}%"


# -------------------------------
#   DUELLI + STORICO + ELO
# -------------------------------
async def sfida_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id
    challenger = message.from_user

    if chat_id in ACTIVE_DUELS and ACTIVE_DUELS[chat_id]["active"]:
        return await message.reply_text("C'è già una sfida attiva in questo gruppo. Finite quella prima.")

    if not message.reply_to_message:
        return await message.reply_text("Usa /sfida rispondendo al messaggio di chi vuoi sfidare.")

    target = message.reply_to_message.from_user
    if target.id == challenger.id:
        return await message.reply_text("Non puoi sfidare te stesso, anche se sei messo male.")

    ACTIVE_DUELS[chat_id] = {
        "active": True,
        "p1_id": str(challenger.id),
        "p2_id": str(target.id),
        "p1_name": challenger.first_name,
        "p2_name": target.first_name,
        "score": {
            str(challenger.id): 0,
            str(target.id): 0,
        },
    }

    await message.reply_text(
        f"⚔️ SFIDA APERTA!\n"
        f"{challenger.first_name} ha sfidato {target.first_name}.\n"
        f"Primo a 3 slot vincenti vince il duello!"
    )


def handle_duel_win(chat_id: int, user_id: str, nome: str, scores: Dict[str, Any]) -> str:
    if chat_id not in ACTIVE_DUELS:
        return ""

    duel = ACTIVE_DUELS[chat_id]
    if not duel["active"]:
        return ""

    if user_id not in duel["score"]:
        return ""

    duel["score"][user_id] += 1
    current = duel["score"][user_id]

    msg = f"\n⚔️ {nome} sale a {current} vittorie nella sfida."

    if current >= 3:
        duel["active"] = False
        p1_id = duel["p1_id"]
        p2_id = duel["p2_id"]
        p1_name = duel["p1_name"]
        p2_name = duel["p2_name"]
        s1 = duel["score"][p1_id]
        s2 = duel["score"][p2_id]

        ensure_user_struct(scores, p1_id, p1_name)
        ensure_user_struct(scores, p2_id, p2_name)

        if s1 > s2:
            winner_id, loser_id = p1_id, p2_id
        else:
            winner_id, loser_id = p2_id, p1_id

        scores[winner_id]["duel_wins"] += 1
        scores[loser_id]["duel_losses"] += 1

        elo_gain, elo_loss = update_elo(winner_id, loser_id, scores)

        duels = load_duels()
        duels.append(
            {
                "p1": p1_name,
                "p2": p2_name,
                "score1": s1,
                "score2": s2,
                "winner": scores[winner_id]["name"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        save_duels(duels)

        msg += (
            f"\n🏁 DUELLO FINITO!\n"
            f"{p1_name} vs {p2_name}: {s1} - {s2}\n"
            f"Vince {scores[winner_id]['name']}!\n\n"
            f"📈 ELO aggiornati:\n"
            f"• {scores[winner_id]['name']}: {scores[winner_id]['elo']} ( +{elo_gain} )\n"
            f"• {scores[loser_id]['name']}: {scores[loser_id]['elo']} ( {elo_loss} )"
        )

    return msg


async def topduelli_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


# -------------------------------
#   ESPANSIONE DEL DOMINIO
# -------------------------------
def is_expansion_active(chat_id: int) -> bool:
    now_ts = datetime.now(timezone.utc).timestamp()
    return EXPANSION_UNTIL.get(chat_id, 0) > now_ts


async def espansione_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    now_ts = datetime.now(timezone.utc).timestamp()
    duration = 4 * 60 + 11

    if is_expansion_active(chat_id):
        return await update.message.reply_text("L'espansione del dominio è già attiva in questo gruppo.")

    EXPANSION_UNTIL[chat_id] = now_ts + duration

    await update.message.reply_text(
        "🌌 *ESPANSIONE DEL DOMINIO ATTIVATA*\n"
        "Per i prossimi 4 minuti e 11 secondi, le slot vincenti vengono ricompensate con più punti\n"
        "e, a volte, la realtà si piega: alcune sconfitte vengono *annullate*.",
        parse_mode="Markdown",
    )


# -------------------------------
#   LOGICA SLOT
# -------------------------------
async def handle_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.dice is None:
        return

    # -------------------------------
    #   BLOCCO SLOT (ADMIN)
    # -------------------------------
    if SLOT_BLOCKED:
        await update.message.reply_text(
            "⛔ Il tracking delle slot è temporaneamente disattivato dall’amministratore.",
            parse_mode="Markdown"
        )
        return


    dice = update.message.dice
    if dice.emoji != "🎰":
        return

    await asyncio.sleep(1)

    message = update.message
    user = message.from_user
    user_id = str(user.id)
    nome = user.first_name
    chat_id = message.chat_id

    users = load_users()
    users[user_id] = nome
    save_users(users)

    scores = load_scores()
    ensure_user_struct(scores, user_id, nome)

    jackpot = (dice.value == 64)

    # -------------------------------
    #   DOMAIN EXPANSION REROLL
    # -------------------------------
    if is_expansion_active(chat_id):
        if scores[user_id]["last_was_win"] and dice.value not in WIN_VALUES:
            if random.random() < 0.35:
                await message.reply_text(
                    "🌌 *ESPANSIONE DEL DOMINIO*\n"
                    "La realtà si distorce… la tua slot è stata *annullata*.",
                    parse_mode="Markdown",
                )
                save_scores(scores)
                return

    # -------------------------------
    #   TRACKING GENERALE
    # -------------------------------
    now_ts = datetime.now(timezone.utc).timestamp()
    last_ts = scores[user_id]["last_slot_ts"]
    scores[user_id]["last_slot_ts"] = now_ts

    scores[user_id]["total_slots"] += 1

    speed_msg = ""
    if last_ts > 0:
        delta = now_ts - last_ts
        if delta > 0:
            speed = 1.0 / delta
            if speed > scores[user_id]["best_speed"]:
                scores[user_id]["best_speed"] = speed
                speed_msg = f"\n⚡ Nuovo record personale di velocità per {nome}: {speed:.3f} slot/s"

    msg = ""

    # -------------------------------
    #   VITTORIA
    # -------------------------------
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
        elif streak == 4:
            scores[user_id]["quad"] += 1
        elif streak == 5:
            scores[user_id]["quint"] += 1

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
            msg += "🌌 *ESPANSIONE DEL DOMINIO ATTIVA* — i punti fluiscono più forti.\n"

        msg += msg_vittoria(nome, jackpot)
        streak_msg = msg_streak(nome, streak)
        if streak_msg:
            msg += f"\n{streak_msg}"

        duel_msg = handle_duel_win(chat_id, user_id, nome, scores)
        if duel_msg:
            msg += f"\n{duel_msg}"

    # -------------------------------
    #   PERDITA
    # -------------------------------
    else:
        scores[user_id]["last_was_win"] = False

        scores[user_id]["streak"] = 0
        scores[user_id]["sfiga"] += 1
        sfiga = scores[user_id]["sfiga"]

        if sfiga > scores[user_id]["best_sfiga"]:
            scores[user_id]["best_sfiga"] = sfiga

        msg = msg_sfiga(nome, sfiga)

    if speed_msg:
        if msg:
            msg += speed_msg
        else:
            msg = speed_msg.lstrip()

    if msg:
        await message.reply_text(msg, parse_mode="Markdown")

    save_scores(scores)


# -------------------------------
#   COMANDI STATS
# -------------------------------
async def score_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        f"• Duelli: {d.get('duel_wins', 0)} vittorie / {d.get('duel_losses', 0)} sconfitte"
    )

    await update.message.reply_text(msg)


async def tope_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def benedici_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    if not users:
        await update.message.reply_text("Non posso benedire nessuno, nessun utente.")
        return

    user_id, name = random.choice(list(users.items()))
    msg = (
        f"✨ *BENEDIZIONE DELLA SLOT*\n"
        f"Oggi il seed si è rivelato a {name}..."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def maledici_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    if not users:
        await update.message.reply_text("Non posso maledire nessuno, nessun utente.")
        return

    user_id, name = random.choice(list(users.items()))
    msg = (
        f"💀 *MALEDIZIONE DELLA SLOT*\n"
        f"{name} è stato scelto.\n"
        f"Per le prossime 5 slot, la matematica riderà di lui."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def invoca_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    nome = user.first_name

    if random.randint(1, 100) == 1:
        testo_mistico = """
        ِسْمِ اللّهِ الرَّحْمـَنِ الرَّحِيمِ
        الْحَمْدُ للّهِ رَبِّ الْعَالَمِينَ
        الرَّحْمـنِ الرَّحِيمِ
        مَـالِكِ يَوْمِ الدِّينِ
        إِيَّاك نَعْبُدُ وإِيَّاكَ نَسْتَعِينُ
        اهدِنَــــا الصِّرَاطَ المُستَقِيمَ
        صِرَاطَ الَّذِينَ أَنعَمتَ عَلَيهِمْ غَيرِ المَغضُوبِ عَلَيهِمْ وَلاَ الضَّالِّينَ

        以最仁慈、最仁慈的上帝之名
        赞美上帝，世界之主
        最仁慈、最仁慈
        审判日的拥有者
        我们要敬拜你，我们向你寻求帮助
        引导我们走上正路
        那些你赐予恩典的人的道路，不是那些受你的愤怒的人，也不是那些误入歧途的人的道路。
        """

        msg = (
            f"{testo_mistico}\n\n"
            f"✨ *BENEDIZIONE DEL PROFETA*\n"
            f"Oggi {nome} è stato scelto."
        )

        await update.message.reply_text(msg, parse_mode="Markdown")


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    scores = load_scores()
    if not scores:
        await update.message.reply_text("Nessun punteggio ancora. Qualcuno tiri una slot! 🎰")
        return

    sorted_players = sorted(scores.items(), key=lambda x: x[1]["points"], reverse=True)

    lines = ["🏆 *CLASSIFICA PUNTI*"]
    for i, (_, d) in enumerate(sorted_players[:10], start=1):
        lines.append(f"{i}. {d['name']} — {d['points']} punti")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def topstreak_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    scores = load_scores()
    if not scores:
        await update.message.reply_text("Nessuna streak registrata.")
        return

    sorted_players = sorted(scores.items(), key=lambda x: x[1]["best_streak"], reverse=True)

    lines = ["🔥 *CLASSIFICA STREAK*"]
    for i, (_, d) in enumerate(sorted_players[:10], start=1):
        lines.append(f"{i}. {d['name']} — {d['best_streak']} di fila")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def topsfiga_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    scores = load_scores()
    if not scores:
        await update.message.reply_text("Nessuna skill issue registrata.")
        return

    sorted_players = sorted(scores.items(), key=lambda x: x[1]["best_sfiga"], reverse=True)

    lines = ["💀 *CLASSIFICA DELLA SKILL ISSUE*"]
    for i, (_, d) in enumerate(sorted_players[:10], start=1):
        lines.append(f"{i}. {d['name']} — {d['best_sfiga']} fallimenti consecutivi")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def topcombo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = (
        "📖 *GUIDA UFFICIALE DELLO SLOTBOT* 🎰\n\n"
        "🎰 *Slot Tracking*\n"
        "• Registro automaticamente ogni slot tirata\n"
        "• Assegno punti solo alle combinazioni vincenti\n"
        "• Gestisco streak 2–5 con bonus e messaggi goliardici\n"
        "• Tengo conto anche della *sfiga* (fallimenti consecutivi)\n"
        "• Traccio quante doppie/triple/poker/cinquine fai\n"
        "• Traccio quante slot totali tiri e la tua winrate\n"
        "• Misuro la tua velocità tra due slot consecutive (slot/s)\n\n"
        "⚔️ *Duelli*\n"
        "• /sfida (in risposta) — Duello al meglio delle 3 vittorie\n"
        "• /topduelli — Classifica duelli\n"
        "• /storicosfide — Ultime 10 sfide\n"
        "• Sistema ELO integrato con /tope\n\n"
        "📊 *Comandi:*\n"
        "• /score — Le tue statistiche personali\n"
        "• /top — Classifica punti\n"
        "• /topstreak — Classifica streak\n"
        "• /topsfiga — Classifica skill issue\n"
        "• /topcombo — Classifica combo\n"
        "• /topwinrate — Classifica winrate\n"
        "• /topspeed — Classifica velocità\n"
        "• /tope — Classifica ELO\n"
        "• /espansione — Attiva l'espansione del dominio\n"
        "• /help — Questo magnifico manuale\n\n"
        "Buona fortuna… ne avrai bisogno. 😈"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


async def sbusta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    if not users:
        await update.message.reply_text("Non c’è nessuno da taggare… gruppo fantasma 👻")
        return

    mentions = " ".join([f"@{name}" for name in users.values() if name])
    msg = f"📦 **È ORA DI SBUSTARE!**\n{mentions}\n\nAndiamo a sbustare?"

    await update.message.reply_text(msg, parse_mode="Markdown")


# -------------------------------
#   MAIN
# -------------------------------
def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("score", score_command))
    app.add_handler(CommandHandler("top", top_command))
    app.add_handler(CommandHandler("topstreak", topstreak_command))
    app.add_handler(CommandHandler("topsfiga", topsfiga_command))
    app.add_handler(CommandHandler("topcombo", topcombo_command))
    app.add_handler(CommandHandler("topwinrate", topwinrate_command))
    app.add_handler(CommandHandler("topspeed", topspeed_command))
    app.add_handler(CommandHandler("topduelli", topduelli_command))
    app.add_handler(CommandHandler("storicosfide", storicosfide_command))
    app.add_handler(CommandHandler("tope", tope_command))

    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("sbusta", sbusta_command))
    app.add_handler(CommandHandler("benedici", benedici_command))
    app.add_handler(CommandHandler("maledici", maledici_command))
    app.add_handler(CommandHandler("invoca", invoca_command))

    app.add_handler(CommandHandler("sfida", sfida_command))
    app.add_handler(CommandHandler("espansione", espansione_command))

    app.add_handler(CommandHandler("setpoints", setpoints_command))
    app.add_handler(CommandHandler("addpoints", addpoints_command))
    app.add_handler(CommandHandler("setstreak", setstreak_command))
    app.add_handler(CommandHandler("setsfiga", setsfiga_command))
    app.add_handler(CommandHandler("exportjson", exportjson_command))
    app.add_handler(CommandHandler("importjson", importjson_command))
    app.add_handler(CommandHandler("blockslot", blockslot_command))
    app.add_handler(CommandHandler("unblockslot", unblockslot_command))


    app.add_handler(MessageHandler(filters.Dice.ALL, handle_dice))

    print("Bot in esecuzione...")
    app.run_polling()


if __name__ == "__main__":
    main()
