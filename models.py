"""
User data models and structure management
"""
from typing import Dict, Any
from config import ELO_K_FACTOR


def ensure_user_struct(scores: Dict[str, Any], user_id: str, nome: str) -> None:
    """Ensure a user has all required fields in scores"""
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
        # Add missing fields for existing users
        scores[user_id].setdefault("name", nome)
        scores[user_id].setdefault("points", 0)
        scores[user_id].setdefault("streak", 0)
        scores[user_id].setdefault("best_streak", 0)
        scores[user_id].setdefault("sfiga", 0)
        scores[user_id].setdefault("best_sfiga", 0)
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


def update_elo(winner_id: str, loser_id: str, scores: Dict[str, Any]) -> tuple:
    """Calculate and update ELO ratings using standard formula
    Returns: (elo_gain_winner, elo_loss_loser)
    """
    Ra = scores[winner_id]["elo"]
    Rb = scores[loser_id]["elo"]

    Ea = 1 / (1 + 10 ** ((Rb - Ra) / 400))
    Eb = 1 / (1 + 10 ** ((Ra - Rb) / 400))

    new_Ra = int(Ra + ELO_K_FACTOR * (1 - Ea))
    new_Rb = int(Rb + ELO_K_FACTOR * (0 - Eb))

    scores[winner_id]["elo"] = new_Ra
    scores[loser_id]["elo"] = new_Rb

    return new_Ra - Ra, new_Rb - Rb
