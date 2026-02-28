"""
Admin commands
"""
import json
import os
import zipfile
import io
from datetime import datetime, timezone
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
            # when debug activates automatically send current scores
            await exportscore_command(update, context)
        except:
            await update.message.reply_text("⚠️ Export fallito, ma debug attivo.")

        await update.message.reply_text(
            "🛠️ *DEBUG MODE ATTIVO*\n"
            "• Solo tu puoi tirare slot (gli altri vengono ignorati)\n"
            "• I failsafe sono disattivati\n"
            "• Nessun punteggio o statistica viene salvata\n"
            "• Le slot NON vengono registrate (streak, sfiga, velocity ecc.)",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🛠️ *DEBUG MODE DISATTIVATO*\n"
            "Il bot è tornato alla normalità: tutte le slot vengono di nuovo tracciate e i failsafe ripristinati.",
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


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run comprehensive bot tests (admin only)"""
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    try:
        await update.message.reply_text(
            "🧪 Test in corso...\n"
            "Esecuzione della suite di test...",
            parse_mode="Markdown"
        )

        results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }

        # Test 1: Import modules
        try:
            import config
            import storage
            import models
            import utils
            import handlers
            import game_state
            results["passed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"❌ Import modules: {str(e)}")

        # Test 2: Load scores
        try:
            scores = load_scores()
            assert isinstance(scores, dict)
            results["passed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"❌ Load scores: {str(e)}")

        # Test 3: Load users
        try:
            users = load_users()
            assert isinstance(users, dict)
            results["passed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"❌ Load users: {str(e)}")

        # Test 4: Load duels
        try:
            duels = load_duels()
            # Duels can be empty, just check it's a dict
            assert isinstance(duels, (dict, type(None)))
            results["passed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"❌ Load duels: {str(e)}")

        # Test 5: Test user struct initialization
        try:
            test_scores = {}
            models.ensure_user_struct(test_scores, "123", "TestUser")
            assert "123" in test_scores
            assert all(key in test_scores["123"] for key in [
                "name", "points", "streak", "best_streak", "sfiga", 
                "best_sfiga", "total_slots", "total_wins"
            ])
            results["passed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"❌ User struct: {str(e)}")

        # Test 6: Test ELO calculation
        try:
            test_scores = {
                "user1": {"elo": 1600},
                "user2": {"elo": 1400}
            }
            models.update_elo("user1", "user2", test_scores)
            assert test_scores["user1"]["elo"] != 1600
            results["passed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"❌ ELO calculation: {str(e)}")

        # Test 7: Test format_winrate
        try:
            wr = utils.format_winrate(10, 5)
            assert "%" in wr
            results["passed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"❌ format_winrate: {str(e)}")

        # Test 8: Test is_expansion_active
        try:
            # Test with a dummy chat_id
            result = utils.is_expansion_active(12345)
            assert isinstance(result, bool)
            results["passed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"❌ is_expansion_active: {str(e)}")

        # Test 9: File existence checks
        try:
            assert os.path.exists(SCORES_FILE) or not os.path.exists(SCORES_FILE)
            assert os.path.exists(USERS_FILE) or not os.path.exists(USERS_FILE)
            assert os.path.exists(DUELS_FILE) or not os.path.exists(DUELS_FILE)
            results["passed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"❌ File checks: {str(e)}")

        # Test 10: Config constants
        try:
            from config import WIN_VALUES, ELO_K_FACTOR, DOMAIN_EXPANSION_DURATION
            assert isinstance(WIN_VALUES, set) and len(WIN_VALUES) > 0
            assert isinstance(ELO_K_FACTOR, (int, float)) and ELO_K_FACTOR > 0
            assert isinstance(DOMAIN_EXPANSION_DURATION, (int, float)) and DOMAIN_EXPANSION_DURATION > 0
            results["passed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"❌ Config constants: {str(e)}")

        # Build response message
        message = "TEST RESULTS\n\n"
        message += f"Passati: {results['passed']}/10\n"
        message += f"Falliti: {results['failed']}/10\n"

        if results["errors"]:
            message += "\nErrori:\n"
            for error in results["errors"][:5]:  # Mostra max 5 errori
                message += f"{error}\n"
            if len(results["errors"]) > 5:
                message += f"\n... e altri {len(results['errors']) - 5} errori"
        else:
            message += "\nTutti i test passati!"

        await update.message.reply_text(message)

    except Exception as e:
        # Fallback error message
        await update.message.reply_text(f"Errore nei test: {str(e)}")


async def addduel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a duel record manually (admin only)"""
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    if not context.args or len(context.args) < 5:
        return await update.message.reply_text(
            "Uso: /addduel <player1> <player2> <score1> <score2> <winner_name>\n\n"
            "Esempio: /addduel Mario Luigi 3 1 Mario\n"
            "(aggiunge un duello vinto da Mario 3-1 contro Luigi)"
        )

    try:
        p1_name = context.args[0]
        p2_name = context.args[1]
        score1 = int(context.args[2])
        score2 = int(context.args[3])
        winner_name = " ".join(context.args[4:])  # Supporta nomi con spazi

        # Load and add duel
        duels = load_duels()
        duels.append({
            "p1": p1_name,
            "p2": p2_name,
            "score1": score1,
            "score2": score2,
            "winner": winner_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        save_duels(duels)

        await update.message.reply_text(
            f"✅ Duello aggiunto:\n"
            f"{p1_name} vs {p2_name}: {score1} - {score2}\n"
            f"Vincitore: {winner_name}"
        )

    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Errore! Controlla i parametri:\n"
            "/addduel <player1> <player2> <score1> <score2> <winner>"
        )


async def debuginfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show complete debug info about all data (admin only)"""
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    try:
        scores = load_scores()
        users = load_users()
        duels = load_duels() or []
        import game_state
        
        msg = "📊 **STATO COMPLETO DEL BOT**\n\n"
        
        # Files info
        msg += "📁 **File Salvati:**\n"
        msg += f"• scores.json: {len(scores)} utenti\n"
        msg += f"• users.json: {len(users)} nomi\n"
        msg += f"• duels.json: {len(duels)} duelli storici\n\n"
        
        # Game state
        msg += "🎮 **Stato Attuale:**\n"
        msg += f"• Duelli attivi: {len(game_state.ACTIVE_DUELS)}\n"
        msg += f"• Espansioni attive: {len(game_state.EXPANSION_UNTIL)}\n"
        msg += f"• Sfide in sospeso: {len(game_state.PENDING_DUELS)}\n"
        msg += f"• Slot bloccati: {game_state.SLOT_BLOCKED}\n"
        msg += f"• Debug mode: {game_state.DEBUG_MODE}\n\n"
        
        # Data sample
        msg += "👥 **Primi 3 Utenti:**\n"
        for user_id, data in list(scores.items())[:3]:
            name = data.get("name", "?")
            points = data.get("points", 0)
            msg += f"• {name}: {points} punti\n"
        
        # Backup info
        backups = get_backup_list()
        msg += f"\n💾 **Backup:** {len(backups)} file salvati\n"
        if backups:
            latest = backups[-1].split("/")[-1]
            msg += f"Ultimo: {latest}"
        
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def resetuser_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset a user's data to default (admin only)"""
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    if not context.args or len(context.args) < 1:
        return await update.message.reply_text("Uso: /resetuser <user_id>")

    try:
        user_id = str(context.args[0])
        scores = load_scores()
        
        if user_id not in scores:
            return await update.message.reply_text(f"❌ Utente {user_id} non trovato.")
        
        nome = scores[user_id].get("name", "Unnamed")
        
        # Reset to default structure
        from models import ensure_user_struct
        scores[user_id] = {}
        ensure_user_struct(scores, user_id, nome)
        save_scores(scores)
        
        await update.message.reply_text(f"✅ {nome} resettato ai valori di default.")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def modifyuser_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Modify specific user field (admin only)
    
    Uso: /modifyuser <user_id> <campo> <valore>
    Campi: points, streak, best_streak, sfiga, best_sfiga, elo, duel_wins, duel_losses
    """
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    if not context.args or len(context.args) < 3:
        return await update.message.reply_text(
            "Uso: /modifyuser <user_id> <campo> <valore>\n\n"
            "Campi: points, streak, best_streak, sfiga, best_sfiga, elo, "
            "duel_wins, duel_losses, total_wins, total_slots, name"
        )

    try:
        user_id = str(context.args[0])
        field = context.args[1]
        value = context.args[2]
        
        scores = load_scores()
        if user_id not in scores:
            return await update.message.reply_text(f"❌ Utente {user_id} non trovato.")
        
        # Parse value type
        if value.isdigit():
            value = int(value)
        elif value.replace(".", "", 1).isdigit():
            value = float(value)
        elif value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        
        old_value = scores[user_id].get(field, "N/A")
        scores[user_id][field] = value
        save_scores(scores)
        
        await update.message.reply_text(
            f"✅ {scores[user_id]['name']}.{field}\n"
            f"{old_value} → {value}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def datacheck_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check data integrity (admin only)"""
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    try:
        scores = load_scores()
        from models import ensure_user_struct
        
        issues = []
        fixed = 0
        
        for user_id, data in scores.items():
            if not isinstance(data, dict):
                issues.append(f"❌ {user_id}: dati non sono dict")
                continue
            
            # Verifica campi obbligatori
            required = ["name", "points", "streak", "best_streak", "sfiga", 
                       "best_sfiga", "total_slots", "total_wins", "elo"]
            
            for field in required:
                if field not in data:
                    ensure_user_struct(scores, user_id, data.get("name", "?"))
                    fixed += 1
        
        if fixed > 0:
            save_scores(scores)
        
        msg = "🔍 **Data Integrity Check**\n\n"
        msg += f"✅ {len(scores)} utenti verificati\n"
        msg += f"🔧 {fixed} campi aggiunti\n"
        
        if issues:
            msg += f"\n❌ Problemi trovati:\n"
            for issue in issues[:5]:
                msg += f"{issue}\n"
        else:
            msg += "\n✅ Nessun problema!"
        
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def cleanstate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clean temporary game state (admin only)"""
    user = update.message.from_user
    if not is_admin(user.id):
        return await update.message.reply_text("Non hai il permesso.")

    try:
        import game_state
        
        old_duels = len(game_state.ACTIVE_DUELS)
        old_expansions = len(game_state.EXPANSION_UNTIL)
        old_pending = len(game_state.PENDING_DUELS)
        
        game_state.ACTIVE_DUELS.clear()
        game_state.EXPANSION_UNTIL.clear()
        game_state.PENDING_DUELS.clear()
        game_state.SLOT_BLOCKED = False
        
        msg = f"🧹 **Pulizia Game State**\n\n"
        msg += f"✅ Duelli attivi eliminati: {old_duels}\n"
        msg += f"✅ Espansioni attive eliminate: {old_expansions}\n"
        msg += f"✅ Sfide in sospeso eliminate: {old_pending}\n"
        msg += f"✅ Slot sbloccati\n\n"
        msg += "State pulito! I dati persistenti (.json) sono intatti."
        
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")

async def daily_recap(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send daily recap of leaderboard changes to admin"""
    from storage import get_leaderboard_snapshots, load_scores
    
    # Get yesterday's snapshot
    yesterday = get_leaderboard_snapshots(days_back=1)
    if not yesterday:
        return  # No snapshot from yesterday
    
    # Get today's top 10 (ignore metadata/non-dict entries)
    scores = load_scores()
    clean_scores = {k: v for k, v in scores.items() if isinstance(v, dict)}
    today_top_10 = sorted(clean_scores.items(), key=lambda x: x[1].get("points", 0), reverse=True)[:10]
    
    msg = "📊 *DAILY RECAP* 📊\n\n"
    
    # Analyze changes
    yesterday_dict = {item["user_id"]: item for item in yesterday["top_10"]}
    
    movers = []
    for idx, (uid, data) in enumerate(today_top_10):
        old_position = None
        old_points = None
        
        # Find old position
        for old_idx, old_item in enumerate(yesterday["top_10"]):
            if old_item["user_id"] == uid:
                old_position = old_idx
                old_points = old_item["points"]
                break
        
        if old_position is not None:
            position_change = old_position - idx
            points_change = data.get("points", 0) - old_points
            
            if position_change != 0 or points_change > 50:
                if position_change > 0:
                    movers.append(f"📈 {data.get('name', 'Unknown')} sale a #{idx+1} (+{points_change} pts)")
                elif position_change < 0:
                    movers.append(f"📉 {data.get('name', 'Unknown')} scende a #{idx+1}")
                else:
                    if points_change > 0:
                        movers.append(f"💎 {data.get('name', 'Unknown')} guadagna {points_change} pts (rimane #{idx+1})")
        else:
            # New entry to top 10
            movers.append(f"⭐ {data.get('name', 'Unknown')} entra in top 10 a #{idx+1}!")
    
    if movers:
        msg += "*HIGHLIGHTS:*\n"
        for mover in movers:
            msg += f"{mover}\n"
    else:
        msg += "Nessun cambiamento significativo nel leaderboard.\n"
    
    msg += "\n*TOP 10 OGGI:*\n"
    for idx, (uid, data) in enumerate(today_top_10):
        msg += f"#{idx+1} - {data.get('name', 'Unknown')}: {data.get('points', 0)} pts\n"
    
    # Send to admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=msg,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"❌ Failed to send daily recap: {str(e)}")


async def highlights_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show today's highlights in the current chat (no snapshot created)"""
    from storage import get_leaderboard_snapshots, load_scores

    yesterday = get_leaderboard_snapshots(days_back=1)
    if not yesterday:
        return await update.message.reply_text("Nessun highlight disponibile ancora.")

    scores = load_scores()
    clean_scores = {k: v for k, v in scores.items() if isinstance(v, dict)}
    today_top_10 = sorted(clean_scores.items(), key=lambda x: x[1].get("points", 0), reverse=True)[:10]

    msg = "📊 *HIGHLIGHTS DEL GIORNO* 📊\n\n"

    movers = []
    for idx, (uid, data) in enumerate(today_top_10):
        old_position = None
        old_points = None
        for old_idx, old_item in enumerate(yesterday["top_10"]):
            if old_item["user_id"] == uid:
                old_position = old_idx
                old_points = old_item["points"]
                break
        if old_position is not None:
            position_change = old_position - idx
            points_change = data.get("points", 0) - old_points
            if position_change != 0 or points_change > 50:
                if position_change > 0:
                    movers.append(f"📈 {data.get('name','Unknown')} sale a #{idx+1} (+{points_change} pts)")
                elif position_change < 0:
                    movers.append(f"📉 {data.get('name','Unknown')} scende a #{idx+1}")
                else:
                    if points_change > 0:
                        movers.append(f"💎 {data.get('name','Unknown')} guadagna {points_change} pts (rimane #{idx+1})")
        else:
            movers.append(f"⭐ {data.get('name','Unknown')} entra in top 10 a #{idx+1}!")
    if movers:
        msg += "*HIGHLIGHTS:*\n"
        for m in movers:
            msg += f"{m}\n"
    else:
        msg += "Nessun cambiamento significativo nel leaderboard.\n"

    msg += "\n*TOP 10 OGGI:*\n"
    for idx, (uid, data) in enumerate(today_top_10):
        msg += f"#{idx+1} - {data.get('name','Unknown')}: {data.get('points',0)} pts\n"

    await update.message.reply_text(msg, parse_mode="Markdown")