#!/bin/sh

echo ""
echo "Select a sender to run:"
echo "  1) Estacion Clima - Real-time"
echo "  2) Estacion Clima - Batch (5-day backfill)"
echo "  3) Cultivo Cacao  - Real-time"
echo "  4) Cultivo Cacao  - Batch (5-day backfill)"
echo ""
printf "Enter choice [1-4]: "
read choice

case "$choice" in
    1) exec python sender_live.py estacion_clima ;;
    2) exec python sender_batch.py estacion_clima ;;
    3) exec python sender_live.py cultivo_cacao ;;
    4) exec python sender_batch.py cultivo_cacao ;;
    *) echo "Invalid choice. Exiting."; exit 1 ;;
esac
