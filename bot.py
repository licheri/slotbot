"""
SlotBot - Main telegram bot application
"""
import os
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

# Config and constants
from config import TOKEN, BACKUP_INTERVAL_HOURS

# Storage auto-recovery
from storage import auto_import_latest_backup

# Admin commands
from commands_admin import (
    debug_command, migrascores_command, setpoints_command, 
    addpoints_command, setstreak_command, setsfiga_command,
    exportscore_command, exportduels_command, exportusers_command, 
    exportall_command, importscore_command, importduels_command,
    importusers_command, importall_command, blockslot_command,
    unblockslot_command, helpadmin_command, backupnow_command,
    listbackups_command, scheduled_backup, test_command, addduel_command,
    debuginfo_command, resetuser_command, modifyuser_command, 
    datacheck_command, cleanstate_command, daily_recap
)

# Stats commands
from commands_stats import (
    score_command, top_command, topstreak_command, topsfiga_command,
    topcombo_command, topwinrate_command, topspeed_command, 
    topduelli_command, storicosfide_command, tope_command
)

# Gameplay commands
from commands_gameplay import (
    sfida_command, espansione_command, benedici_command, 
    maledici_command, invoca_command, sbusta_command, help_command
)

# Easter egg commands
from commands_easter_eggs import slot_command, sfidabot_command

# Mini-games commands
from commands_minigames import tarocchi_command, lotteria_command, evento_command

# Handlers
from handlers import handle_dice


def main() -> None:
    """Start the bot"""
    # Auto-import latest backup at startup (for Railway auto-recovery)
    print("🔄 Avvio del bot...", flush=True)
    auto_import_latest_backup()
    print("✅ Dati carichi", flush=True)
    
    app = ApplicationBuilder().token(TOKEN).build()

    # Schedule automated backup every 12 hours (but not on startup)
    app.job_queue.run_repeating(
        scheduled_backup, 
        interval=60 * 60 * BACKUP_INTERVAL_HOURS
    )
    
    # Schedule daily recap at 22:00 UTC
    from datetime import time
    app.job_queue.run_daily(
        daily_recap,
        time=time(hour=22, minute=0)
    )
    
    # Save leaderboard snapshot every day at 23:55 UTC
    from storage import save_leaderboard_snapshot
    app.job_queue.run_daily(
        lambda ctx: save_leaderboard_snapshot(),
        time=time(hour=23, minute=55)
    )

    # ============================================================
    #   STATS COMMANDS
    # ============================================================
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

    # ============================================================
    #   GAMEPLAY COMMANDS
    # ============================================================
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("sbusta", sbusta_command))
    app.add_handler(CommandHandler("benedici", benedici_command))
    app.add_handler(CommandHandler("maledici", maledici_command))
    app.add_handler(CommandHandler("invoca", invoca_command))
    app.add_handler(CommandHandler("sfida", sfida_command))
    app.add_handler(CommandHandler("espansione", espansione_command))
    app.add_handler(CommandHandler("slot", slot_command))
    app.add_handler(CommandHandler("sfidabot", sfidabot_command))

    # ============================================================
    #   MINI-GAMES COMMANDS
    # ============================================================
    app.add_handler(CommandHandler("tarocchi", tarocchi_command))
    app.add_handler(CommandHandler("lotteria", lotteria_command))
    app.add_handler(CommandHandler("evento", evento_command))

    # ============================================================
    #   ADMIN COMMANDS
    # ============================================================
    app.add_handler(CommandHandler("debug", debug_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("addduel", addduel_command))
    app.add_handler(CommandHandler("debuginfo", debuginfo_command))
    app.add_handler(CommandHandler("resetuser", resetuser_command))
    app.add_handler(CommandHandler("modifyuser", modifyuser_command))
    app.add_handler(CommandHandler("datacheck", datacheck_command))
    app.add_handler(CommandHandler("cleanstate", cleanstate_command))
    app.add_handler(CommandHandler("setpoints", setpoints_command))
    app.add_handler(CommandHandler("addpoints", addpoints_command))
    app.add_handler(CommandHandler("setstreak", setstreak_command))
    app.add_handler(CommandHandler("setsfiga", setsfiga_command))
    app.add_handler(CommandHandler("blockslot", blockslot_command))
    app.add_handler(CommandHandler("unblockslot", unblockslot_command))

    # ============================================================
    #   EXPORT COMMANDS
    # ============================================================
    app.add_handler(CommandHandler("exportscore", exportscore_command))
    app.add_handler(CommandHandler("exportduels", exportduels_command))
    app.add_handler(CommandHandler("exportusers", exportusers_command))
    app.add_handler(CommandHandler("exportall", exportall_command))

    # ============================================================
    #   IMPORT COMMANDS
    # ============================================================
    app.add_handler(CommandHandler("importscore", importscore_command))
    app.add_handler(CommandHandler("importduels", importduels_command))
    app.add_handler(CommandHandler("importusers", importusers_command))
    app.add_handler(CommandHandler("importall", importall_command))

    # ============================================================
    #   BACKUP COMMANDS
    # ============================================================
    app.add_handler(CommandHandler("migrascores", migrascores_command))
    app.add_handler(CommandHandler("backupnow", backupnow_command))
    app.add_handler(CommandHandler("listbackups", listbackups_command))
    app.add_handler(CommandHandler("helpadmin", helpadmin_command))

    # ============================================================
    #   GAME LOGIC
    # ============================================================
    app.add_handler(MessageHandler(filters.Dice.ALL, handle_dice))

    print("🎰 SlotBot avviato!")
    app.run_polling()


if __name__ == "__main__":
    main()
