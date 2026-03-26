#!/bin/sh

echo ""
echo "Select a sender to run:"
echo "  1) Estacion Clima - Real-time"
echo "  2) Estacion Clima - Batch (5-day backfill)"
echo "  3) Cacao Cultivo  - Real-time"
echo "  4) Cacao Cultivo  - Batch (5-day backfill)"
echo ""
printf "Enter choice [1-4]: "
read choice

case "$choice" in
    1) exec python IoTCentralSender_EstacionClimaExterno.py ;;
    2) exec python "IoTCentralSenderBatch_EstacionClimaExterno..py" ;;
    3) exec python IoTCentralSender_CultivoCacao.py ;;
    4) exec python IoTCentralSenderBatch_CultivoCacao.py ;;
    *) echo "Invalid choice. Exiting."; exit 1 ;;
esac
