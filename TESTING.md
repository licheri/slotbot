# SlotBot - Testing & Local Development

## 🧪 Local Testing (No Railways Deploy Needed!)

### Quick Test Everything
```bash
./test_local.sh
```
This runs all checks without needing a deployed bot:
- ✅ Python syntax check
- ✅ Module imports
- ✅ Game logic functions
- ✅ Utility functions

Takes ~2 seconds and doesn't touch Railways!

### Before Each Deploy to Railways
```bash
./test_local.sh  # Must pass before pushing
```

## 🚀 Deploy to Railways

### First Time Setup
```bash
# Create .env file with your real token
cp .env.example .env
# Edit .env and add real TOKEN and ADMIN_ID
```

### Deploy
```bash
git add -A
git commit -m "your message"
git push  # This triggers Railway auto-deploy
```

## 🐛 Troubleshooting

### If tests fail
Look at the error and check:
1. **Import errors** → Check file dependencies in REFACTORING.md
2. **Function errors** → The function signature changed
3. **Config errors** → Check config.py constants

### If Railways deploy fails
1. Check the logs in Railway dashboard
2. Make sure TOKEN and ADMIN_ID are set in Railway environment
3. Run `./test_local.sh` first to catch issues early

## 📝 Test Results

Current status: ✅ **ALL TESTS PASSING**

Last test run results:
- 10 modules load successfully
- All imports clean
- All game functions work
- All utilities functioning

## 💡 Development Workflow

```
Make changes
    ↓
./test_local.sh  (Must pass!)
    ↓
git commit & push
    ↓
Railway auto-deploys
```

This way you catch 95% of errors locally before wasting time on deployment!

## 🆘 Common Issues

### `TOKEN not set`
- Locally: Already handled by test_local.sh
- Railway: Add TOKEN environment variable in Railway dashboard

### `Module not found`
- Run `./test_local.sh` to check all imports
- Check REFACTORING.md for dependency info

### `Command not registered`
- Restart the bot
- Check bot.py for the handler registration

## ✅ Pre-Deploy Checklist

Before pushing to Railways:
- [ ] Run `./test_local.sh` - must pass
- [ ] Check git diff - no accidental changes
- [ ] Commit message is clear
- [ ] TOKEN is set in Railway env vars

Then push with confidence! 🚀
