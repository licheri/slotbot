# SlotBot 🎰

A feature-rich Telegram slot machine bot with comprehensive stats tracking, player duels, achievements, and mini-games.

## Features

### 🎰 Core Slot System
- **Automatic tracking** of all slot rolls in a group
- **Points system** with bonus multipliers for streaks
- **Win detection** (combinations: 64, 63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43)
- **Streak tracking** with special bonuses:
  - Double (2 wins): +1 point
  - Triple (3 wins): +1 point + domain expansion notification
  - Quadrupla (4 wins): +2 points
  - Cinquina (5 wins): +3 points
- **Failure tracking** (sfiga) with personal records
- **Speed measurement** (slots per second) with personal best tracking
- **Total statistics** (total rolls, total wins, winrate %)

### ⚔️ Duel System
- **Two-stage duels**: Challenge someone and they must respond to accept
- **Best-of-3 format**: First to 3 wins takes the match
- **Turn-based gameplay**: Only current player's rolls count
- **ELO rating system** with automatic calculation based on opponent strength
- **Historical tracking**: View all past duel results with `/storicosfide`
- **Leaderboard**: ELO rankings with `/tope`

### 🌌 Domain Expansion
- **Triple requirement**: Get a triple to unlock domain expansion
- **10-message window**: Must activate within 10 messages after the triple
- **33% reroll chance**: Failed rolls have 33% chance to be cancelled (Hakari-style)
- **Duration**: Expansion lasts for 4 minutes and 11 seconds
- **Bonus points**: +1 point per win during expansion

### 🏆 Achievement System
An unlock-based achievement system with 12 total badges:

- 🩸 **First Blood** - Win your first slot
- ⚡ **Streak Master** - Achieve a 5-win streak
- 🔥 **Unstoppable** - Achieve a 10-win streak
- 👑 **Triple Crown** - Land a triple
- ♠️ **Poker Face** - Land a quadrupla
- 💎 **Perfect Five** - Land a cinquina
- ⚔️ **Duelist** - Win your first duel
- 🤖 **Bot Slayer** - Defeat the bot in combat
- 🔮 **Tarot Reader** - Read the daily tarot
- 🎰 **Lottery Winner** - Win the weekly lottery
- ⚡ **Event Master** - Participate in a Sunday event
- 💨 **Speed Demon** - Set a new personal speed record
- 💥 **Sfogo** - Usato /bestemmia dopo 50 sfighe

All achievements are displayed in `/score` and persisted across bot restarts.

### 🎲 Mini-Games

#### Tarocchi (Daily Tarot)
- **Frequency**: Once per day
- **Cards**: 22 unique tarot cards with personalized prophecies
- **Command**: `/tarocchi`
- **Achievement**: Tarot Reader

#### Lotteria (Weekly Lottery)
- **Frequency**: Once per week
- **Mechanics**: 
  - Pick a random number (1-100)
  - 20% base win chance + exact match bonus
  - **Jackpot**: Accumulates 50 points per week for non-winners
- **Command**: `/lotteria`
- **Achievement**: Lottery Winner
- **Max Winnings**: Jackpot + random(100-500) points

#### Evento (Sunday Event)
- **Frequency**: Sundays only, once per week
- **Random events**:
  - 🎲 **Quick Duel**: Roll 3 dice, win points based on victory count (10/20/30)
  - 🏃 **Speed Challenge**: Roll as much as possible in 10 seconds
  - 🎰 **Lucky Combination**: Guess a number, hit within 3 rolls = 50 points
  - 🎲 **Russian Roulette**: Win = triple your daily points, lose = -10 points
  - 🧠 **Memory Game**: Guess 3 random numbers
- **Command**: `/evento`
- **Achievement**: Event Master

### 🤖 Bot Interactions

#### /slot - Bot Rolls
- **Frequency**: Once per day per player
- **Mechanics**: Bot rolls 1-10 times and reports results
- **Achievement**: Not directly tracked but cool easter egg

#### /sfidabot - Challenge the Bot
- **Frequency**: Once per day per player
- **Format**: Best-of-3 like player vs player
- **Points**: Counted in duel_wins/duel_losses
- **Achievement**: Bot Slayer (when you win)

#### /bestemmia - Vent Your Frustration
- **Requirement**: You need at least a 50‑loss streak (`sfiga >= 50`)
- **Cooldown**: Once every 50 additional losses (tracked automatically)
- **Mechanics**: lets you *sfogarti* with a brutal curse message
- **Achievement**: Sfogo (unlocked on first use)

### 📊 Statistics & Leaderboards

**Personal Stats** - `/score`
- ELO rating
- Total points
- Total slots rolled
- Win/loss ratio
- Current and best streaks
- Current and best failures (sfiga)
- Combo counts (doubles, triples, poker, cinquine)
- Speed record (slots/second)
- Duel record
- Domains used
- All achievements earned

**Leaderboards**:
- `/top` - Points ranking
- `/topstreak` - Best current streaks
- `/topsfiga` - Best consecutive failures (for fun)
- `/topcombo` - Combo record (doubles, triples, etc.)
- `/topwinrate` - Win percentage
- `/topspeed` - Fastest slot/s
- `/topduelli` - Duel wins
- `/tope` - ELO ratings
- `/storicosfide` - Last 10 duel results
- `/highlights` - Show daily highlights (no manual savepoint)

### 📅 Daily Recap
Every day at 22:00 UTC, the bot automatically sends the admin:
- **Leaderboard changes**: Position movements, point gains, new top 10 entries
- **Highlights**: Significant movers and big point gains
- **Current top 10**: Full ranking snapshot

⚙️ *Puoi richiamare gli highlights in qualsiasi momento usando il comando `/highlights` (non crea un nuovo savepoint, la copia giornaliera viene gestita automaticamente alle 20).* 

### 🛡️ Anti-Cheat Safeguards
- **Forwarded message detection**: Can't forward rolls
- **Edited message detection**: Can't edit past rolls
- **Bot relay detection**: Can't use other bots to roll
- **Debug mode**: Admin-only with `/debug` command

### 🔧 Admin Commands

**Data Management**:
- `/debuginfo` - Complete bot state overview
- `/resetuser <user_id>` - Reset user to default stats
- `/modifyuser <id> <field> <value>` - Modify any user field
- `/datacheck` - Verify and auto-fix data integrity
- `/cleanstate` - Clear temporary game state

**Points Management**:
- `/setpoints <user_id> <points>` - Set exact points
- `/addpoints <user_id> <points>` - Add points
- `/setstreak <user_id> <num>` - Set current streak
- `/setsfiga <user_id> <num>` - Set current failures

**Duel Management**:
- `/addduel <p1> <p2> <winner>` - Add historical duel record

**Backup & Export**:
- `/backupnow` - Trigger immediate backup
- `/listbackups` - Show all backup files
- `/exportscore`, `/exportduels`, `/exportusers`, `/exportall` - Export data (now includes leaderboard snapshots)
- `/importscore`, `/importduels`, `/importusers`, `/importall` - Import data

**Server Control**:
- `/blockslot` - Disable slot tracking
- `/unblockslot` - Re-enable slot tracking
- `/test` - Test command
- `/debug` - Toggle debug mode

**Help**:
- `/helpadmin` - Admin command reference

## 📁 File Structure

```
slotbot/
├── bot.py                    # Main entry point & handler registration
├── config.py                 # Configuration & constants
├── models.py                 # User data structures & achievements
├── storage.py                # JSON file I/O & backup management
├── handlers.py               # Dice roll handler & game logic
├── utils.py                  # Utility functions & message formatting
├── game_state.py             # Temporary game state (duels, expansions, etc.)
│
├── commands_stats.py          # Leaderboard & personal stats
├── commands_gameplay.py       # Duels, domain expansion, buffs
├── commands_easter_eggs.py    # Bot rolling & bot duels
├── commands_minigames.py      # Tarocchi, lotteria, evento
├── commands_admin.py          # Admin tools & data management
│
├── test_comprehensive.py      # Full test suite (34 tests)
├── requirements.txt           # Python dependencies
├── scores.json               # Player statistics (persistent)
├── users.json                # Username mappings
├── duels.json                # Historical duel records
├── backup/                   # Automatic daily backups (ZIP format)
└── leaderboard_snapshots/    # Daily top 10 snapshots for recap
```

## 🗄️ Data Persistence

### Main Data Files
- **scores.json**: All player statistics (24 fields per user)
- **users.json**: Username mappings for ID lookup
- **duels.json**: Complete historical duel records

### Data Fields per User
```json
{
  "name": "string",
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
  "last_was_win": false,
  "last_triple_msg_id": null,
  "domains_used": 0,
  "last_slot_bot_ts": 0,
  "last_duel_bot_ts": 0,
  "last_tarocchi_ts": 0,
  "last_lotteria_ts": 0,
  "last_evento_ts": 0,
  "achievements": ["achievement_id", ...]
}
```

### Automatic Backup System
- **Frequency**: Every 12 hours
- **Format**: ZIP file containing scores.json, users.json, duels.json
- **Location**: `backup/` directory
- **Auto-Recovery**: Latest backup automatically imported on bot startup
- **Retention**: Keeps last 10 backups

## ⚙️ Setup & Deployment

### Requirements
- Python 3.10+
- python-telegram-bot 21.6
- Telegram Bot Token (set as `TOKEN` in config.py)

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set your bot token
export TELEGRAM_BOT_TOKEN="your_token_here"
# Or edit config.py

# Run locally for testing
python3 bot.py
```

### Deployment (Railway)
The bot is optimized for Railway's ephemeral filesystem:
- Data automatically backs up every 12 hours
- Latest backup auto-imports on startup
- No manual recovery needed after redeploy

## 🧪 Testing

Run the comprehensive test suite:
```bash
python3 test_comprehensive.py
```

**Coverage** (34/34 tests):
- User structure initialization
- Score loading/saving
- Win/loss detection
- Streak tracking
- Duel mechanics (two-stage acceptance, turn-based gameplay)
- Domain expansion mechanics
- Speed tracking
- ELO calculations
- Achievement unlocking
- And more...

## 🎮 Gameplay Flow

1. **Setup**: Player joins group and tips a slot with `/slot` or sends a 🎰 emoji
2. **Tracking**: Bot automatically records roll, calculates result, updates stats
3. **Streaks**: Back-to-back wins trigger streak bonuses and special messages
4. **Tripled**: At 3-win streak, player can `/espansione` within 10 messages
5. **Duels**: Players challenge each other with `/sfida` → opponent responds with `/sfida` → best-of-3 match
6. **Mini-Games**: Daily tarot, weekly lottery, weekly events for variety
7. **Achievements**: Unlock badges as you reach milestones
8. **Recap**: Daily admin recap shows leaderboard movements

## 🔐 Security

- **No hardcoded secrets**: Token loaded from environment
- **Git ignore**: `.env` and sensitive files excluded
- **Admin-only commands**: All admin functions check `ADMIN_ID`
- **Anti-cheat**: Multiple layers prevent fraudulent rolls
  - Forward detection
  - Edit detection
  - Bot relay detection

## 📈 Performance

- **Fast response times**: JSON-based storage is snappy for group use
- **Automatic cleanup**: Old backups automatically removed (keeps last 10)
- **Memory efficient**: Game state is temporary, persisted data is minimal
- **Batch operations**: Backup and recovery runs efficiently

## 🤝 Contributing

When adding new features:
1. Add new fields to `models.ensure_user_struct()` 
2. Add to `models.get_leaderboard_snapshots()` if needed
3. Add to backup functions in `storage.py`
4. Update achievement definitions if applicable
5. Add tests to `test_comprehensive.py`
6. Update this README

## 📝 Version History

- **v2.0** (Feb 2026): Major refactor from monolithic to modular architecture
  - Split bot.py (1500+ lines) → 11 focused modules
  - Added achievement system
  - Added mini-games (tarocchi, lotteria, evento)
  - Added daily recap system
  - Implemented auto-recovery for Railway
  - Turn-based duel system redesign

- **v1.0**: Initial release with basic slot tracking

## 🎯 Future Ideas

- Monthly season resets with special challenges
- Clan system for group competitions
- Rare "golden slot" events with special rewards
- Betting system between players
- Seasonal achievements
- Custom slot themes per group
- Webhook alternative to polling for faster response

---

**Made with 💜 by matteo**  
SlotBot v2.0 - Fully modular, persistent, and achievement-driven.
