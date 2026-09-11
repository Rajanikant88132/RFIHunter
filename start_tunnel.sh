#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# RFI Hunter — Start public HTTPS tunnel via ngrok
# Usage:  ./start_tunnel.sh
# ──────────────────────────────────────────────────────────────
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "🔍  Checking Docker services..."
docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null | grep -v "^$"

echo ""
echo "🔒  Starting HTTPS tunnel on port 443..."
pkill ngrok 2>/dev/null || true
sleep 1

nohup ngrok http 443 --host-header=localhost --log=stdout > /tmp/rfihunter-ngrok.log 2>&1 &
NGROK_PID=$!
echo "   ngrok PID: $NGROK_PID"

# Wait up to 10s for ngrok API to be ready
for i in $(seq 1 10); do
  sleep 1
  PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); ts=d.get('tunnels',[]); print(next((t['public_url'] for t in ts if t['proto']=='https'),''))" 2>/dev/null)
  if [ -n "$PUBLIC_URL" ]; then break; fi
done

if [ -z "$PUBLIC_URL" ]; then
  echo "❌  ngrok tunnel failed to start. Check /tmp/rfihunter-ngrok.log"
  exit 1
fi

echo ""
echo "══════════════════════════════════════════════════════════"
echo "  ✅  RFI Hunter is live!"
echo ""
echo "  🌐  Public URL (internet):   $PUBLIC_URL"
echo "  🔒  Local HTTPS (LAN):       https://$(ipconfig getifaddr en0 2>/dev/null || echo '192.168.x.x')"
echo "  🔒  Local HTTPS (localhost): https://localhost"
echo "  🔁  HTTP (auto-redirects):   http://localhost"
echo ""
echo "  📊  Dashboard:    $PUBLIC_URL"
echo "  🔌  API stats:    $PUBLIC_URL/api/stats"
echo "  🔍  ngrok console: http://localhost:4040"
echo "══════════════════════════════════════════════════════════"
echo ""
echo "  Press Ctrl+C to stop the tunnel (Docker services keep running)"
echo ""

# Keep script alive and show log tail
trap "pkill ngrok; echo 'Tunnel stopped.'; exit 0" INT TERM
wait $NGROK_PID
