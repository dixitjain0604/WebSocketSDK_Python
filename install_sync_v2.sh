#!/bin/bash
# install_sync_v2.sh — Install the rewritten sync system
# ========================================================
# Usage:
#   1. Copy sync_users_biz.py, views_sync.py, sync_users.html, and
#      this script into your SDK root folder
#   2. cd "/home/batman/Downloads/WebSocketSDK 20250611/WebSocketSDK_Python"
#   3. bash install_sync_v2.sh
#
# What it does:
#   - Copies sync_users_biz.py → DjangoExample/sdkdemoapp/biz/
#   - Copies views_sync.py     → DjangoExample/sdkdemoapp/
#   - Copies sync_users.html   → DjangoExample/sdkdemoapp/templates/sdkdemoapp/
#   - Patches urls.py to add the /sync_users route (if not already present)

set -e

SDK_ROOT="$(cd "$(dirname "$0")" && pwd)"
DJANGO_DIR="$SDK_ROOT/DjangoExample"
APP_DIR="$DJANGO_DIR/sdkdemoapp"
BIZ_DIR="$APP_DIR/biz"
TPL_DIR="$APP_DIR/templates/sdkdemoapp"

echo "=== Install Sync v2 ==="
echo "SDK root: $SDK_ROOT"
echo ""

# 1. Copy business logic
echo "[1/4] Installing sync_users_biz.py..."
cp "$SDK_ROOT/sync_users_biz.py" "$BIZ_DIR/sync_users_biz.py"
echo "  → $BIZ_DIR/sync_users_biz.py"

# 2. Copy view
echo "[2/4] Installing views_sync.py..."
cp "$SDK_ROOT/views_sync.py" "$APP_DIR/views_sync.py"
echo "  → $APP_DIR/views_sync.py"

# 3. Copy template
echo "[3/4] Installing sync_users.html..."
mkdir -p "$TPL_DIR"
cp "$SDK_ROOT/sync_users.html" "$TPL_DIR/sync_users.html"
echo "  → $TPL_DIR/sync_users.html"

# 4. Patch urls.py
URLS_FILE="$DJANGO_DIR/demosite/urls.py"
echo "[4/4] Patching urls.py..."

if grep -q "sync_users_view" "$URLS_FILE" 2>/dev/null; then
    echo "  → Already patched (sync_users_view found in urls.py)"
else
    # Add import
    if ! grep -q "from sdkdemoapp.views_sync" "$URLS_FILE"; then
        sed -i '/^from django/a from sdkdemoapp.views_sync import sync_users_view' "$URLS_FILE"
        echo "  → Added import"
    fi

    # Add URL pattern
    if ! grep -q "sync_users" "$URLS_FILE"; then
        sed -i "/urlpatterns/,/]/ {
            /]/ i\\    path('sync_users', sync_users_view, name='sync_users'),
        }" "$URLS_FILE"
        echo "  → Added URL pattern"
    fi
fi

echo ""
echo "=== DONE ==="
echo ""
echo "Now restart Django:"
echo "  cd \"$DJANGO_DIR\""
echo "  python manage.py runserver 0.0.0.0:8000 --settings=demosite.settings.development"
echo ""
echo "Then visit: http://127.0.0.1:8000/sync_users"
