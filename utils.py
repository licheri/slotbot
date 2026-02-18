"""
Utility functions for messages, formatting, and common operations
"""
from typing import Dict
from datetime import datetime, timezone
from config import DOMAIN_EXPANSION_DURATION


def format_winrate(total_wins: int, total_slots: int) -> str:
    """Format winrate percentage"""
    if total_slots == 0:
        return "0.00%"
    perc = (total_wins / total_slots) * 100
    return f"{perc:.2f}%"


def is_expansion_active(chat_id: int) -> bool:
    """Check if domain expansion is active in chat"""
    import game_state
    now_ts = datetime.now(timezone.utc).timestamp()
    return game_state.EXPANSION_UNTIL.get(chat_id, 0) > now_ts


def msg_vittoria(nome: str, jackpot: bool) -> str:
    """Victory message"""
    if jackpot:
        return f"💥 JACKPOT! {nome} no vabbé assurdo!"
    return f"🎉 {nome} ha max slottato!"


def msg_streak(nome: str, streak: int) -> str:
    """Streak message"""
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
    """Skill issue message"""
    if sfiga >= 50 and sfiga % 10 == 0:
        return f"💀 {nome} ha le skill issues: {sfiga} slot senza vincere."
    return ""
