#!/bin/bash
# Get logs from Railway deployment

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Railway Logs Fetcher${NC}\n"

# Check if railway is installed
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}Railway CLI non trovato.${NC}"
    echo ""
    echo "Opzioni:"
    echo "1) Installa Railway CLI:"
    echo "   npm install -g @railway/cli"
    echo ""
    echo "2) Oppure usa il dashboard online:"
    echo "   https://railway.app -> Seleziona il progetto -> Logs"
    echo ""
    echo "3) Se su Windows/Mac senza npm, scarica da:"
    echo "   https://railway.app/cli"
    exit 1
fi

# Check if user is logged in
if ! railway token &> /dev/null; then
    echo -e "${YELLOW}⚠️  Non sei loggato a Railway${NC}"
    echo "Esegui: railway login"
    exit 1
fi

echo -e "${GREEN}📡 Connessione a Railway...${NC}\n"

# Get latest logs
case "${1:-follow}" in
    follow)
        echo -e "${BLUE}Live logs (Ctrl+C per fermare):${NC}\n"
        railway logs --follow
        ;;
    tail)
        NUM=${2:-50}
        echo -e "${BLUE}Ultimi $NUM log:${NC}\n"
        railway logs | tail -n "$NUM"
        ;;
    save)
        FILE=${2:-railway_logs.txt}
        echo -e "${BLUE}Salvataggio log in $FILE...${NC}"
        railway logs > "$FILE"
        echo -e "${GREEN}✅ Salvato: $FILE${NC}"
        echo "Apri con: cat $FILE"
        ;;
    *)
        echo "Uso:"
        echo "  ./get_logs.sh follow     # Live logs (default)"
        echo "  ./get_logs.sh tail [N]   # Ultimi N log (default 50)"
        echo "  ./get_logs.sh save FILE  # Salva in file"
        ;;
esac
