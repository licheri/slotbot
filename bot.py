import json
import os
import asyncio
from typing import Dict, Any
import random
from datetime import datetime, timezone
import zipfile 
import io
import glob


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
DEBUG_MODE = False
CURRENT_JSON_VERSION = 2


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

async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global DEBUG_MODE

    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    # toggle
    DEBUG_MODE = not DEBUG_MODE

    if DEBUG_MODE:
        # EXPORT AUTOMATICO
        try:
            await exportjson_command(update, context)
        except:
            await update.message.reply_text("⚠️ Export fallito, ma debug attivo.")

        await update.message.reply_text(
            "🛠️ *DEBUG MODE ATTIVO*\n"
            "• Solo tu puoi tirare slot\n"
            "• I failsafe sono disattivati",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🛠️ *DEBUG MODE DISATTIVATO*\n"
            "Il bot è tornato alla normalità.",
            parse_mode="Markdown"
        )

async def migrascores_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    scores = load_scores()
    migrated = migrate_scores(scores)
    save_scores(migrated)

    await update.message.reply_text("🔧 Scores migrati alla nuova struttura.")


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

async def exportscore_command(update, context):
    if not is_admin(update.message.from_user.id):
        return

    try:
        with open("scores.json", "rb") as f:
            await update.message.reply_document(
                document=f,
                filename="scores.json",
                caption="📤 Ecco *scores.json*",
                parse_mode="Markdown"
            )
    except:
        await update.message.reply_text("⚠️ scores.json non trovato.")

async def exportduels_command(update, context):
    if not is_admin(update.message.from_user.id):
        return

    try:
        with open("duels.json", "rb") as f:
            await update.message.reply_document(
                document=f,
                filename="duels.json",
                caption="📤 Ecco *duels.json*",
                parse_mode="Markdown"
            )
    except:
        await update.message.reply_text("⚠️ duels.json non trovato.")

async def exportusers_command(update, context):
    if not is_admin(update.message.from_user.id):
        return

    try:
        with open("users.json", "rb") as f:
            await update.message.reply_document(
                document=f,
                filename="users.json",
                caption="📤 Ecco *users.json*",
                parse_mode="Markdown"
            )
    except:
        await update.message.reply_text("⚠️ users.json non trovato.")

async def exportall_command(update, context): 
    if not is_admin(update.message.from_user.id): 
        return 
    
    buffer = io.BytesIO() 
   
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z: 
        for filename in ["scores.json", "duels.json", "users.json"]: 
            try: 
                z.write(filename) 
            except: 
                pass 
        
        buffer.seek(0) 
        await update.message.reply_document( 
            document=buffer, 
            filename="slotbot_backup.zip", 
            caption="📦 Backup completo del bot", 
            parse_mode="Markdown" )

async def importscore_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    # Deve essere una reply a un messaggio con documento
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text(
            "Usa /importscore *rispondendo* a un messaggio che contiene `scores.json`.",
            parse_mode="Markdown"
        )

    doc = update.message.reply_to_message.document
    file = await doc.get_file()
    content = await file.download_as_bytearray()

    try:
        scores = json.loads(content.decode("utf-8"))
        scores = migrate_scores(scores)
        save_scores(scores)
        await update.message.reply_text("📥 scores.json importato e migrato.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Errore nell'import di scores.json:\n{e}")
async def importduels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text(
            "Usa /importduels *rispondendo* a un messaggio che contiene `duels.json`.",
            parse_mode="Markdown"
        )

    doc = update.message.reply_to_message.document
    file = await doc.get_file()
    content = await file.download_as_bytearray()

    try:
        duels = json.loads(content.decode("utf-8"))
        duels = migrate_duels(duels)
        save_duels(duels)
        await update.message.reply_text("📥 duels.json importato e migrato.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Errore nell'import di duels.json:\n{e}")
async def importusers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text(
            "Usa /importusers *rispondendo* a un messaggio che contiene `users.json`.",
            parse_mode="Markdown"
        )

    doc = update.message.reply_to_message.document
    file = await doc.get_file()
    content = await file.download_as_bytearray()

    try:
        users = json.loads(content.decode("utf-8"))
        users = migrate_users(users)
        save_users(users)
        await update.message.reply_text("📥 users.json importato e migrato.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Errore nell'import di users.json:\n{e}")

async def importall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text(
            "Usa /importall *rispondendo* a un file ZIP contenente scores.json, duels.json e users.json.",
            parse_mode="Markdown"
        )

    doc = update.message.reply_to_message.document
    file = await doc.get_file()
    content = await file.download_as_bytearray()

    try:
        z = zipfile.ZipFile(io.BytesIO(content))
    except:
        return await update.message.reply_text("⚠️ Il file non è uno ZIP valido.")

    # SCORES
    try:
        scores = json.loads(z.read("scores.json").decode("utf-8"))
        scores = migrate_scores(scores)
        save_scores(scores)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Errore in scores.json:\n{e}")

    # DUELS
    try:
        duels = json.loads(z.read("duels.json").decode("utf-8"))
        duels = migrate_duels(duels)
        save_duels(duels)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Errore in duels.json:\n{e}")

    # USERS
    try:
        users = json.loads(z.read("users.json").decode("utf-8"))
        users = migrate_users(users)
        save_users(users)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Errore in users.json:\n{e}")

    await update.message.reply_text("📥 Import completo eseguito.")


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

async def helpadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        return  # Non mostra nulla agli altri

    msg = (
        "🛠️ *Pannello Admin — SlotBot*\n"
        "Ecco tutti i comandi amministrativi disponibili:\n\n"

        "🔧 *Modalità Debug / Sicurezza*\n"
        "• /debug — Attiva/disattiva debug mode (ignora tutti tranne te, no score, no failsafe)\n"
        "• /togglefailsafe — Attiva/disattiva i failsafe anti-cheat\n\n"

        "📤 *Export JSON*\n"
        "• /exportscore — Esporta scores.json\n"
        "• /exportduels — Esporta duels.json\n"
        "• /exportusers — Esporta users.json\n"
        "• /exportall — Esporta tutti i JSON in un unico ZIP\n\n"

        "📥 *Import JSON*\n"
        "• /importscore — Importa scores.json (rispondi al file)\n"
        "• /importduels — Importa duels.json (rispondi al file)\n"
        "• /importusers — Importa users.json (rispondi al file)\n"
        "• /importall — Importa ZIP con scores.json, duels.json, users.json\n\n"

        "🧬 *Migrazione*\n"
        "• /migrascores — Migra manualmente scores.json alla versione corrente\n\n"

        "📦 *Backup*\n"
        "• /backupnow — Crea un backup ZIP immediato e te lo invia\n"
        "• /listbackups — Mostra i backup salvati in /backup/\n\n"

        "⏱️ *Backup automatico*\n"
        "• Ogni 12h viene creato un backup ZIP\n"
        "• Viene inviato a te\n"
        "• Mantiene solo gli ultimi 10\n"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


# -------------------------------
#   STORAGE
# -------------------------------


def create_backup_zip():
    os.makedirs("backup", exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
    zip_path = f"backup/backup_{timestamp}.zip"

    # CREA IL FILE ZIP
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for filename in ["scores.json", "duels.json", "users.json"]:
            if os.path.exists(filename):
                z.write(filename)

    # MANTIENI SOLO GLI ULTIMI 10 BACKUP
    backups = sorted(glob.glob("backup/backup_*.zip"))
    if len(backups) > 10:
        for old in backups[:-10]:
            try:
                os.remove(old)
            except:
                pass

    return zip_path


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

def migrate_scores(scores):
    version = scores.get("_version", 1)

    # MIGRAZIONE DA VERSIONE 1 → 2
    if version < 2:
        for user_id, d in scores.items():
            if user_id.startswith("_"):
                continue

            d.setdefault("domains_used", 0)
            d.setdefault("last_triple_msg_id", None)
            d.setdefault("best_speed", 0.0)

        scores["_version"] = 2

    return scores

def migrate_duels(duels):
    duels.setdefault("_version", CURRENT_JSON_VERSION)
    return duels

def migrate_users(users):
    users.setdefault("_version", CURRENT_JSON_VERSION)
    return users


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
            "last_triple_msg_id": None,
            "domains_used": 0
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
        scores[user_id].setdefault("last_triple_msg_id", None)
        scores[user_id].setdefault("domains_used", 0)


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


async def scheduled_backup(context):
    zip_path = create_backup_zip()

    # INVIA IL BACKUP A TE (ADMIN)
    try:
        await context.bot.send_document(
            chat_id=ADMIN_ID,
            document=open(zip_path, "rb"),
            caption="📦 Backup automatico eseguito."
        )
    except:
        pass


# -------------------------------
#   ESPANSIONE DEL DOMINIO
# -------------------------------
def is_expansion_active(chat_id: int) -> bool:
    now_ts = datetime.now(timezone.utc).timestamp()
    return EXPANSION_UNTIL.get(chat_id, 0) > now_ts

async def espansione_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    if update.message.message_id - last_triple > 10:
        return await update.message.reply_text(
            "⏳ La finestra di attivazione è scaduta.\n"
            "La TRIPLA non risuona più con il dominio."
        )

    if is_expansion_active(chat_id):
        return await update.message.reply_text("Il dominio è già attivo.")

    now_ts = datetime.now(timezone.utc).timestamp()
    EXPANSION_UNTIL[chat_id] = now_ts + (4 * 60 + 11)

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
            # frase epica stile Hakari, subito dopo l’immagine
            await update.message.reply_text(
                f"{user.first_name} non ha mai imparato la acquisito la tecnica inversa, ma…\n"
                f"l’energia infinita che trabocca da {user.first_name} "
                "forza la realtà istintivamente a riscriversi da sola pur di proteggerlo.\n\n"
                f"In altre parole, per 4 minuti e 11 secondi dopo una tripla, {user.first_name} è di fatto *immortale*.”",
                parse_mode="Markdown"
            )

    except Exception as e:
        await update.message.reply_text(
            "⚠️ Errore nel caricare l'immagine del dominio.",
            parse_mode="Markdown"
        )



# -------------------------------
#   LOGICA SLOT
# -------------------------------
async def handle_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.dice is None:
        return

    # >>> DEBUG MODE: ignora tutti tranne l'admin
    if DEBUG_MODE:
        if update.message.from_user.id != ADMIN_ID:
            return  # gli altri non possono tirare slot


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

    # ============================================================
    #   FAILSAFE ANTI-CHEAT COMPLETO
    # ============================================================

    if not DEBUG_MODE:
        # 1) BLOCCO MESSAGGI INOLTRATI (PTB 20+ SAFE)
        fwd_user = getattr(update.message, "forward_from", None)
        fwd_chat = getattr(update.message, "forward_from_chat", None)

        if fwd_user or fwd_chat:
            await update.message.reply_text(
                "❌ Non puoi inoltrare una slot. Nice try.",
                parse_mode="Markdown"
            )
            return

        # 2) BLOCCO MESSAGGI MODIFICATI
        if getattr(update.message, "edit_date", None):
            await update.message.reply_text(
                "❌ Slot modificata? Non funziona così.",
                parse_mode="Markdown"
            )
            return

        # 3) BLOCCO MESSAGGI INVIATI VIA BOT
        if getattr(update.message, "via_bot", None):
            await update.message.reply_text(
                "❌ Non puoi usare bot esterni per tirare slot.",
                parse_mode="Markdown"
            )
            return

        # 4) BLOCCO SLOT NON AUTENTICHE (dice mancante o spoofato)
        dice_obj = getattr(update.message, "dice", None)
        if dice_obj is None:
            await update.message.reply_text(
                "❌ Questo non è un vero tiro di slot.",
                parse_mode="Markdown"
            )
            return


        # # 5) BLOCCO SLOT TROPPO VECCHIE (anti-spoof)
        # msg_age = datetime.now(timezone.utc).timestamp() - update.message.date.timestamp()
        # if msg_age > 10:  # 10 secondi
        #     await update.message.reply_text(
        #         "❌ Non puoi usare slot vecchie.",
        #         parse_mode="Markdown"
        #     )
        #     return

    # ============================================================
    #   FINE FAILSAFE
    # ============================================================


    # Notifica fine dominio
    if chat_id in EXPANSION_UNTIL:
        if EXPANSION_UNTIL[chat_id] < datetime.now(timezone.utc).timestamp():
            await update.message.reply_text(
                "🌌 *Il dominio si dissolve.*\n"
                "La realtà torna stabile.",
                parse_mode="Markdown"
            )
            EXPANSION_UNTIL[chat_id] = 0


    # misura subito la velocità, PRIMA dello sleep
    now_ts = datetime.now(timezone.utc).timestamp()
    last_ts = scores[user_id]["last_slot_ts"]
    scores[user_id]["last_slot_ts"] = now_ts

    # poi fai lo sleep per non spoilerare l’animazione
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
            if random.random() < 0.33:  # probabilità stile Hakari
                
                # Cancella la slot dell’utente
                try:
                    await context.bot.delete_message(
                        chat_id=chat_id,
                        message_id=message.message_id
                    )
                except:
                    pass  # se non può cancellare, ignora

                # Messaggio epico stile Idle Death Gamble
                await update.message.reply_text(
                    "🌌 *IDLE DEATH GAMBLE*\n"
                    "La tua sconfitta è stata *cancellata*.",
                    parse_mode="Markdown"
                )

                return  # IGNORA COMPLETAMENTE LA SLOT

    # -------------------------------
    #   TRACKING GENERALE
    # -------------------------------
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
            # >>> NEW — Messaggio stile Hakari quando diventi idoneo al dominio
            await message.reply_text(
                f"🎲 *JACKPOT PROBABILITY RISING*\n"
                f"{nome} ha ottenuto una *TRIPLA*.\n"
                f"L’energia del dominio vibra attorno a lui…\n"
                f"Può attivare l’ESPANSIONE entro i prossimi *10 messaggi*.",
                parse_mode="Markdown"
            )

            scores[user_id]["last_triple_msg_id"] = message.message_id
 
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
            msg += "🌌 *ESPANSIONE DEL DOMINIO ATTIVA*\n"

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
        f"• Duelli: {d.get('duel_wins', 0)} vittorie / {d.get('duel_losses', 0)} sconfitte\n"
        f"• Domini espansi: {d.get('domains_used', 0)}\n"
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

async def backupnow_command(update, context):
    if not is_admin(update.message.from_user.id):
        return

    zip_path = create_backup_zip()

    await update.message.reply_document(
        document=open(zip_path, "rb"),
        filename=os.path.basename(zip_path),
        caption="📦 Backup manuale eseguito."
    )

async def listbackups_command(update, context):
    if not is_admin(update.message.from_user.id):
        return

    backups = sorted(glob.glob("backup/backup_*.zip"))

    if not backups:
        return await update.message.reply_text("Nessun backup trovato.")

    msg = "📦 *Backup disponibili:*\n\n"
    for b in backups:
        msg += f"• `{os.path.basename(b)}`\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


# -------------------------------
#   MAIN
# -------------------------------
def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    # Backup ogni 12 ore
    app.job_queue.run_repeating(scheduled_backup, interval=60*60*12, first=10)


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

    app.add_handler(CommandHandler("debug", debug_command))
    app.add_handler(CommandHandler("setpoints", setpoints_command))
    app.add_handler(CommandHandler("addpoints", addpoints_command))
    app.add_handler(CommandHandler("setstreak", setstreak_command))
    app.add_handler(CommandHandler("setsfiga", setsfiga_command))
    app.add_handler(CommandHandler("blockslot", blockslot_command))
    app.add_handler(CommandHandler("unblockslot", unblockslot_command))

    app.add_handler(CommandHandler("exportscore", exportscore_command))
    app.add_handler(CommandHandler("exportduels", exportduels_command))
    app.add_handler(CommandHandler("exportusers", exportusers_command))
    app.add_handler(CommandHandler("exportall", exportall_command))

    app.add_handler(CommandHandler("importscore", importscore_command))
    app.add_handler(CommandHandler("importduels", importduels_command))
    app.add_handler(CommandHandler("importusers", importusers_command))
    app.add_handler(CommandHandler("importall", importall_command))

    app.add_handler(CommandHandler("migrascores", migrascores_command))

    app.add_handler(CommandHandler("backupnow", backupnow_command))
    app.add_handler(CommandHandler("listbackups", listbackups_command))

    app.add_handler(CommandHandler("helpadmin", helpadmin_command))



    app.add_handler(MessageHandler(filters.Dice.ALL, handle_dice))

    print("Bot in esecuzione...")
    app.run_polling()


if __name__ == "__main__":
    main()
