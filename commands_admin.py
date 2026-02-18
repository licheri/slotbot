"""
Admin commands
"""
import json
import os
import zipfile
import io
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID, SCORES_FILE, USERS_FILE, DUELS_FILE
from storage import (
    load_scores, save_scores, load_duels, save_duels, 
    load_users, save_users, migrate_scores, migrate_duels, 
    migrate_users, create_backup_zip, get_backup_list, 
    create_export_zip
)


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id == ADMIN_ID


async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle debug mode (admin only)"""
    import game_state
    
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    game_state.DEBUG_MODE = not game_state.DEBUG_MODE

    if game_state.DEBUG_MODE:
        try:
            await exportscore_command(update, context)
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
    """Manually migrate scores (admin only)"""
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    scores = load_scores()
    migrated = migrate_scores(scores)
    save_scores(migrated)

    await update.message.reply_text("🔧 Scores migrati alla nuova struttura.")


async def setpoints_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user points (admin only)"""
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
    """Add points to user (admin only)"""
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
    """Set user streak (admin only)"""
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
    """Set user sfiga (admin only)"""
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
    """Export scores.json (admin only)"""
    if not is_admin(update.message.from_user.id):
        return

    try:
        with open(SCORES_FILE, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=SCORES_FILE,
                caption="📤 Ecco *scores.json*",
                parse_mode="Markdown"
            )
    except:
        await update.message.reply_text("⚠️ scores.json non trovato.")


async def exportduels_command(update, context):
    """Export duels.json (admin only)"""
    if not is_admin(update.message.from_user.id):
        return

    try:
        with open(DUELS_FILE, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=DUELS_FILE,
                caption="📤 Ecco *duels.json*",
                parse_mode="Markdown"
            )
    except:
        await update.message.reply_text("⚠️ duels.json non trovato.")


async def exportusers_command(update, context):
    """Export users.json (admin only)"""
    if not is_admin(update.message.from_user.id):
        return

    try:
        with open(USERS_FILE, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=USERS_FILE,
                caption="📤 Ecco *users.json*",
                parse_mode="Markdown"
            )
    except:
        await update.message.reply_text("⚠️ users.json non trovato.")


async def exportall_command(update, context):
    """Export all JSON as ZIP (admin only)"""
    if not is_admin(update.message.from_user.id):
        return

    buffer = create_export_zip()

    await update.message.reply_document(
        document=buffer,
        filename="slotbot_backup.zip",
        caption="📦 Backup completo del bot",
        parse_mode="Markdown"
    )


async def importscore_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Import scores.json (admin only)"""
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

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
    """Import duels.json (admin only)"""
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
    """Import users.json (admin only)"""
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
    """Import all JSON from ZIP (admin only)"""
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
        scores = json.loads(z.read(SCORES_FILE).decode("utf-8"))
        scores = migrate_scores(scores)
        save_scores(scores)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Errore in scores.json:\n{e}")

    # DUELS
    try:
        duels = json.loads(z.read(DUELS_FILE).decode("utf-8"))
        duels = migrate_duels(duels)
        save_duels(duels)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Errore in duels.json:\n{e}")

    # USERS
    try:
        users = json.loads(z.read(USERS_FILE).decode("utf-8"))
        users = migrate_users(users)
        save_users(users)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Errore in users.json:\n{e}")

    await update.message.reply_text("📥 Import completo eseguito.")


async def blockslot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Block slot tracking (admin only)"""
    import game_state
    
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    game_state.SLOT_BLOCKED = True

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
    """Unblock slot tracking (admin only)"""
    import game_state
    
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    game_state.SLOT_BLOCKED = False

    await update.message.reply_text(
        "✅ *SLOT TRACKING RIATTIVATO*\n"
        "Il bot ora registra di nuovo tutte le slot.",
        parse_mode="Markdown"
    )


async def helpadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin help (admin only)"""
    user = update.message.from_user
    if not is_admin(user.id):
        return

    msg = (
        "🛠️ *Pannello Admin — SlotBot*\n"
        "Ecco tutti i comandi amministrativi disponibili:\n\n"

        "🔧 *Modalità Debug / Sicurezza*\n"
        "• /debug — Attiva/disattiva debug mode (ignora tutti tranne te, no score, no failsafe)\n\n"

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


async def backupnow_command(update, context):
    """Create backup immediately (admin only)"""
    if not is_admin(update.message.from_user.id):
        return

    zip_path = create_backup_zip()

    await update.message.reply_document(
        document=open(zip_path, "rb"),
        filename=os.path.basename(zip_path),
        caption="📦 Backup manuale eseguito."
    )


async def listbackups_command(update, context):
    """List available backups (admin only)"""
    if not is_admin(update.message.from_user.id):
        return

    backups = get_backup_list()

    if not backups:
        return await update.message.reply_text("Nessun backup trovato.")

    msg = "📦 *Backup disponibili:*\n\n"
    for b in backups:
        msg += f"• `{os.path.basename(b)}`\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def scheduled_backup(context):
    """Scheduled backup task"""
    from config import ADMIN_ID
    zip_path = create_backup_zip()

    try:
        await context.bot.send_document(
            chat_id=ADMIN_ID,
            document=open(zip_path, "rb"),
            caption="📦 Backup automatico eseguito."
        )
    except:
        pass
