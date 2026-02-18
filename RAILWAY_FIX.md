# 🚨 Railway Conflict Error - Bot Running Twice

Se vedi questo errore nei log di Railway:
```
telegram.error.Conflict: Conflict: terminated by other getUpdates request; 
make sure that only one bot instance is running
```

## ✅ Soluzione Veloce

Il bot sta girando in **due istanze contemporaneamente** su Railway. Questo accade dopo un deploy.

### Opzione 1: Restart Manuale (CONSIGLIATO)
1. Vai su https://railway.app
2. Seleziona il tuo progetto **slotbot**
3. Clicca su **Deploy** (in alto)
4. Aspetta 30 secondi per il restart automatico
5. Controlla i log con: `./get_logs.sh follow`

### Opzione 2: Cancella Variabili d'Ambiente (se rimane rotto)
1. Su https://railway.app, vai a **Settings** → **Environment**
2. Nota il valore di `TOKEN` (copioincollalo da qualche parte)
3. Cancella **tutte** le variabili
4. Aggiungi di nuovo solo:
   ```
   TOKEN=tuo_token
   ADMIN_ID=tuo_id
   ```
5. Railway auto-deploy

### Opzione 3: Force Stop & Deploy
```bash
# Sul terminale (se hai Railway CLI):
railway stop
sleep 5
git push  # Trigger new deploy
```

---

## ℹ️ Perché Accade?

Railway a volte non killira completamente la vecchia istanza quando fai deploy nuovo. Così due processi cercano di leggere i messaggi Telegram = **Conflict**.

**Non è un bug del codice!** È un problema di timing su Railway.

---

## ✅ Verifiche Post-Fix

Dopo il restart:

```bash
# 1. Check logs
./get_logs.sh follow

# 2. Dovresti vedere SOLO una volta:
#    🎰 SlotBot avviato!
#    (non due volte)

# 3. Testa il bot
/help    # Dovrebbe rispondere subito
```

Se vedi ancora **Conflict** dopo 5 minuti, usa **Opzione 2** (cancella env vars).

---

## 📊 Log Puliti Dopo Fix

Dopo il restart corretto, vedrai:
```
[inf] Starting Container
[inf] 🎰 SlotBot avviato!
[inf] ... waiting for updates ...
```

**Non** vedrai più questi errori:
```
[err] telegram.error.Conflict: Conflict: terminated by other getUpdates request
```

---

**Risolto?** Tutto torna normale. Railway auto-deploy al prossimo git push.
