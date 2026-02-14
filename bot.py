import json
import os
import asyncio
from typing import Dict, Any
import random


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

# Valori vincenti della slot Telegram 🎰
WIN_VALUES = {1, 22, 43, 64}


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


USERS_FILE = "users.json"

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
    if sfiga >= 50 and sfiga%10 == 0:
        return f"💀 {nome} ha le skill issues: {sfiga} slot senza vincere."
    return ""


# -------------------------------
#   LOGICA SLOT
# -------------------------------
async def handle_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.dice is None:
        return

    dice = update.message.dice

    # Consideriamo solo la slot 🎰
    if dice.emoji != "🎰":
        return

    # Delay per non spoilerare l’animazione
    await asyncio.sleep(1)

    user = update.message.from_user
    user_id = str(user.id)
    nome = user.first_name

    # registra utente per easter egg
    users = load_users()
    users[user_id] = nome
    save_users(users)


    scores = load_scores()

    # Inizializzazione utente
    if user_id not in scores:
        scores[user_id] = {
            "name": nome,
            "points": 0,
            "streak": 0,
            "best_streak": 0,
            "sfiga": 0,
            "best_sfiga": 0
        }
    else:
        scores[user_id]["name"] = nome

    jackpot = (dice.value == 64)

    # -------------------------------
    #   VITTORIA
    # -------------------------------
    if dice.value in WIN_VALUES:
        # reset sfiga
        scores[user_id]["sfiga"] = 0

        # incrementa streak
        scores[user_id]["streak"] += 1
        streak = scores[user_id]["streak"]

        # aggiorna best streak
        if streak > scores[user_id]["best_streak"]:
            scores[user_id]["best_streak"] = streak

        # punti base
        if jackpot:
            scores[user_id]["points"] += 2
        else:
            scores[user_id]["points"] += 1

        # bonus streak
        if streak == 2:
            scores[user_id]["points"] += 1
        elif streak == 3:
            scores[user_id]["points"] += 1
        elif streak == 4:
            scores[user_id]["points"] += 2
        elif streak == 5:
            scores[user_id]["points"] += 3

        # messaggi
        msg = msg_vittoria(nome, jackpot)
        streak_msg = msg_streak(nome, streak)
        if streak_msg:
            msg += f"\n{streak_msg}"

        await update.message.reply_text(msg)

    # -------------------------------
    #   NON VITTORIA
    # -------------------------------
    else:
        # reset streak
        scores[user_id]["streak"] = 0

        # incrementa sfiga
        scores[user_id]["sfiga"] += 1
        sfiga = scores[user_id]["sfiga"]

        # aggiorna best sfiga
        if sfiga > scores[user_id]["best_sfiga"]:
            scores[user_id]["best_sfiga"] = sfiga

        # messaggio solo se sfiga alta
        msg = msg_sfiga(nome, sfiga)
        if msg:
            await update.message.reply_text(msg)

    save_scores(scores)


# -------------------------------
#   COMANDI
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

    msg = (
        f"📊 Statistiche di {d['name']}:\n"
        f"• Punti totali: {d['points']}\n"
        f"• Streak attuale: {d['streak']}\n"
        f"• Record streak: {d['best_streak']}\n"
        f"• Skill issue attuale: {d['sfiga']}\n"
        f"• Record skill issue: {d['best_sfiga']}"
    )

    await update.message.reply_text(msg)


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

import random

async def invoca_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    nome = user.first_name

    # probabilità 1/100
    if random.randint(1, 100) == 1:
        # QUI INSERISCI TU IL TESTO SACRO O MISTICO
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

    await update.message.reply_text("\n".join(lines))


async def topstreak_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    scores = load_scores()
    if not scores:
        await update.message.reply_text("Nessuna streak registrata.")
        return

    sorted_players = sorted(scores.items(), key=lambda x: x[1]["best_streak"], reverse=True)

    lines = ["🔥 *CLASSIFICA STREAK*"]
    for i, (_, d) in enumerate(sorted_players[:10], start=1):
        lines.append(f"{i}. {d['name']} — {d['best_streak']} di fila")

    await update.message.reply_text("\n".join(lines))


async def topsfiga_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    scores = load_scores()
    if not scores:
        await update.message.reply_text("Nessuna skill issue registrata.")
        return

    sorted_players = sorted(scores.items(), key=lambda x: x[1]["best_sfiga"], reverse=True)

    lines = ["💀 *CLASSIFICA DELLA SKILL ISSUE*"]
    for i, (_, d) in enumerate(sorted_players[:10], start=1):
        lines.append(f"{i}. {d['name']} — {d['best_sfiga']} fallimenti consecutivi")

    await update.message.reply_text("\n".join(lines))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = (
        "📖 *GUIDA UFFICIALE DELLO SLOTBOT* 🎰\n\n"
        "Ecco cosa posso fare nel gruppo:\n\n"
        "🎰 *Slot Tracking*\n"
        "• Registro automaticamente ogni slot tirata\n"
        "• Assegno punti solo alle combinazioni vincenti\n"
        "• Gestisco streak 2–5 con bonus e messaggi goliardici\n"
        "• Tengo conto anche della *sfiga* (fallimenti consecutivi)\n\n"
        "📊 *Comandi disponibili:*\n"
        "• /score — Le tue statistiche personali\n"
        "• /top — Classifica punti\n"
        "• /topstreak — Classifica delle streak più alte\n"
        "• /topsfiga — Classifica dei più skill issued\n"
        "• /help — Questo magnifico manuale\n\n"
        "💡 *Tip:* Non rispondo subito alla slot per non spoilerare il risultato.\n"
        "⏳ Lascio finire l’animazione e poi giudico.\n\n"
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
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("sbusta", sbusta_command))
    app.add_handler(CommandHandler("benedici", benedici_command))
    app.add_handler(CommandHandler("maledici", maledici_command))

    app.add_handler(CommandHandler("invoca", invoca_command))

    app.add_handler(MessageHandler(filters.Dice.ALL, handle_dice))

    print("Bot in esecuzione...")
    app.run_polling()


if __name__ == "__main__":
    main()
