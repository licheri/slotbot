"""
Gameplay commands - duels, buffs, domain expansion, etc.
"""
import random
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from storage import load_scores, save_scores, load_duels, save_duels, load_users, save_users
from models import ensure_user_struct, update_elo, unlock_achievement
from utils import is_expansion_active
import game_state


# This will be updated when sfida_command is called
ACTIVE_DUELS = {}


async def sfida_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Challenge someone to a duel (2-stage: challenge + acceptance)"""
    message = update.message
    chat_id = message.chat_id
    challenger = message.from_user

    # Check if there's already an active duel
    if chat_id in game_state.ACTIVE_DUELS:
        return await message.reply_text("C'è già una sfida attiva in questo gruppo. Finite quella prima.")

    if not message.reply_to_message:
        return await message.reply_text("Usa /sfida rispondendo al messaggio di chi vuoi sfidare.")

    target = message.reply_to_message.from_user
    if target.id == challenger.id:
        return await message.reply_text("Non puoi sfidare te stesso, anche se sei messo male.")

    challenger_id = str(challenger.id)
    target_id = str(target.id)

    # Check if there's a pending challenge from the target to challenger
    pending_key = (chat_id, target_id)
    if pending_key in game_state.PENDING_DUELS and game_state.PENDING_DUELS[pending_key] == challenger.id:
        # ACCETTAZIONE: il challenger risponde alla sfida del target
        # Inizia il duello vero e proprio
        del game_state.PENDING_DUELS[pending_key]
        
        game_state.ACTIVE_DUELS[chat_id] = {
            "p1_id": target_id,
            "p2_id": challenger_id,
            "p1_name": target.first_name,
            "p2_name": challenger.first_name,
            "current_turn": target_id,  # Il target inizia (era lui che aveva sfidato)
            "score": {
                target_id: 0,
                challenger_id: 0,
            },
        }

        await message.reply_text(
            f"⚔️ SFIDA ACCETTATA!\n"
            f"{target.first_name} vs {challenger.first_name}\n\n"
            f"🎲 Turno: {target.first_name} (manda uno slot a testa, a turni!)\n"
            f"Primo a 3 vittorie vince!"
        )
        return

    # SFIDA NUOVA: challenge non ancora accettato
    pending_key = (chat_id, challenger_id)
    game_state.PENDING_DUELS[pending_key] = target.id

    await message.reply_text(
        f"⚔️ SFIDA LANCIATA!\n"
        f"{challenger.first_name} ha sfidato {target.first_name}.\n\n"
        f"@{target.username or target.first_name}, rispondi con /sfida a questo messaggio per accettare!"
    )


def handle_duel_turn(chat_id: int, user_id: str, nome: str, scores, won: bool = False) -> str:
    """Handle duel turn - either a win or a loss counts as using up your turn.

    The caller should pass ``won=True`` when the player rolled a winning slot.
    Returns a message to be appended to the slot result (or empty string).
    """
    if chat_id not in game_state.ACTIVE_DUELS:
        return ""

    duel = game_state.ACTIVE_DUELS[chat_id]

    # Check if it's this player's turn
    if duel["current_turn"] != user_id:
        current_name = duel["p1_name"] if duel["p1_id"] == duel["current_turn"] else duel["p2_name"]
        return f"\n⚔️ Non è il tuo turno! Tocca a {current_name}."

    if user_id not in duel["score"]:
        return ""

    # Determine opponent info
    opponent_id = duel["p2_id"] if duel["p1_id"] == user_id else duel["p1_id"]
    opponent_name = duel["p2_name"] if duel["p1_id"] == user_id else duel["p1_name"]

    msg = ""
    if won:
        # register the win
        duel["score"][user_id] += 1
        current = duel["score"][user_id]
        msg = f"\n🎯 {nome} vince il round! ({current}-{duel['score'][opponent_id]})\n"
    else:
        # lost round, no score increment
        msg = f"\n💥 {nome} perde il round! ({duel['score'][user_id]}-{duel['score'][opponent_id]})\n"

    # Always pass turn to opponent
    duel["current_turn"] = opponent_id
    msg += f"📍 Prossimo turno: {opponent_name}"

    # If it was a winning round, check if duel ended
    if won and duel["score"][user_id] >= 3:
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

        msg = (
            f"\n🏁 DUELLO FINITO!\n"
            f"{p1_name} vs {p2_name}: {s1} - {s2}\n"
            f"Vince {scores[winner_id]['name']}!\n\n"
            f"📈 ELO aggiornati:\n"
            f"• {scores[winner_id]['name']}: {scores[winner_id]['elo']} ( +{elo_gain} )\n"
            f"• {scores[loser_id]['name']}: {scores[loser_id]['elo']} ( {elo_loss} )"
        )

        del game_state.ACTIVE_DUELS[chat_id]

    return msg


async def espansione_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activate domain expansion (requires triple)"""
    from config import DOMAIN_EXPANSION_DURATION, DOMAIN_EXPANSION_MESSAGE_WINDOW
    import game_state
    
    chat_id = update.message.chat_id
    user = update.message.from_user
    user_id = str(user.id)

    scores = load_scores()
    ensure_user_struct(scores, user_id, user.first_name)

    last_triple = scores[user_id].get("last_triple_msg_id", None)
    if last_triple is None:
        return await update.message.reply_text(
            "❌ Non puoi espandere il dominio senza una *TRIPLA*."
        )

    if update.message.message_id - last_triple > DOMAIN_EXPANSION_MESSAGE_WINDOW:
        return await update.message.reply_text(
            "⏳ La finestra di attivazione è scaduta.\n"
            "La TRIPLA non risuona più con il dominio."
        )
        scores[user_id]["last_triple_msg_id"] = None
        save_scores(scores)


    if is_expansion_active(chat_id):
        return await update.message.reply_text("Il dominio è già attivo.")

    now_ts = datetime.now(timezone.utc).timestamp()
    game_state.EXPANSION_UNTIL[chat_id] = now_ts + DOMAIN_EXPANSION_DURATION

    # contatore domini
    scores[user_id]["domains_used"] += 1
    save_scores(scores)

    # Invio immagine dominio
    try:
        with open("immagini/dominio.jpg", "rb") as img:
            await update.message.reply_photo(
                photo=img,
                caption=(
                    "🌌 *IDLE DEATH GAMBLE — DOMAIN EXPANSION*"
                ),
                parse_mode="Markdown"
            )
            # frase epica stile Hakari, subito dopo l'immagine
            await update.message.reply_text(
                f"{user.first_name} non ha mai acquisito la tecnica inversa, ma…\n"
                f"l'energia infinita che trabocca da {user.first_name} "
                "forza la realtà istintivamente a riscriversi da sola pur di proteggerlo.\n\n"
                f"In altre parole, per 4 minuti e 11 secondi dopo una tripla, {user.first_name} è di fatto *immortale*.",
                parse_mode="Markdown"
            )

    except Exception as e:
        await update.message.reply_text(
            "⚠️ Errore nel caricare l'immagine del dominio.",
            parse_mode="Markdown"
        )


async def benedici_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bless a random user"""
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
    """Curse a random user"""
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
    """Random prophecy command"""
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


async def sbusta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tag all users"""
    users = load_users()
    if not users:
        await update.message.reply_text("Non c'è nessuno da taggare… gruppo fantasma 👻")
        return

    mentions = " ".join([f"@{name}" for name in users.values() if name])
    msg = f"📦 **È ORA DI SBUSTARE!**\n{mentions}\n\nAndiamo a sbustare?"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def bestemmia_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permit a user to vent a curse once every 50 losing slots"""
    user = update.message.from_user
    user_id = str(user.id)

    scores = load_scores()
    ensure_user_struct(scores, user_id, user.first_name)

    sfiga = scores[user_id].get("sfiga", 0)
    last_baseline = scores[user_id].get("last_bestemmia_sfiga", 0)

    if sfiga < 50:
        return await update.message.reply_text(
            "❌ Hai bisogno di almeno 50 skill issues consecutive per poter bestemmiare!"
        )

    if sfiga - last_baseline < 50:
        needed = last_baseline + 50 - sfiga
        return await update.message.reply_text(
            f"🛑 Hai già bestemmiato di recente. Ti servono ancora {needed} skill issues prima di poterlo fare di nuovo."
        )

    # Allow the vent and record baseline
    scores[user_id]["last_bestemmia_sfiga"] = sfiga
    unlock_achievement(scores, user_id, "bestemmia")
    save_scores(scores)

    await update.message.reply_text(
        "🔥 *PORCO DIO* 🔥",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help menu"""
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
        "• /bestemmia — Sfoga la tua frustrazione (richiede 50 sfighe)\n"
        "• /help — Questo magnifico manuale\n\n"
        # make clear easter eggs are intentionally excluded
        "_Nota: alcuni comandi easter-egg (es. /slot, /sfidabot, /lotteria) non sono elencati qui._\n\n"
        "Buona fortuna… ne avrai bisogno. 😈"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")
