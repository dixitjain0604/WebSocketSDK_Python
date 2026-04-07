#!/bin/bash
# Remove Sync Users from Django web UI
# Keeps sync_engine.py untouched

SDK="/home/batman/Downloads/WebSocketSDK 20250611/WebSocketSDK_Python"
D="$SDK/DjangoExample"

echo "========================================"
echo "  Removing Sync Users from Web UI"
echo "========================================"

# 1. Remove from navbar
echo "[1/3] Removing navbar link..."
sed -i '/[Ss]ync.*[Uu]sers/d' "$D/sdkdemoapp/templates/master.html"
echo "  Done"

# 2. Remove URL route
echo "[2/3] Removing URL route..."
sed -i '/sync_users/d' "$D/sdkdemoapp/urls.py"
echo "  Done"

# 3. Remove view function and import from views.py
echo "[3/3] Removing view function from views.py..."
sed -i '/from .biz import sync_users/d' "$D/sdkdemoapp/views.py"

# Remove the sync_users function (from def to end of file)
LINE=$(grep -n "^def sync_users" "$D/sdkdemoapp/views.py" | head -1 | cut -d: -f1)
if [ -n "$LINE" ]; then
    sed -i "${LINE},\$d" "$D/sdkdemoapp/views.py"
    # Remove trailing blank lines
    sed -i -e :a -e '/^\n*$/{$d;N;ba' -e '}' "$D/sdkdemoapp/views.py"
    echo "  Removed sync_users function from line $LINE"
else
    echo "  No sync_users function found (already clean)"
fi

echo ""
echo "========================================"
echo "  Verifying..."
echo "========================================"
echo "Navbar sync references:"
grep -n "sync" "$D/sdkdemoapp/templates/master.html" || echo "  None (clean)"
echo ""
echo "URLs sync references:"
grep -n "sync" "$D/sdkdemoapp/urls.py" || echo "  None (clean)"
echo ""
echo "Views sync references:"
grep -n "sync" "$D/sdkdemoapp/views.py" || echo "  None (clean)"
echo ""
echo "sync_engine.py still exists:"
ls -la "$SDK/sync_engine.py" 2>/dev/null || echo "  Not found (place it in SDK root)"
echo ""
echo "========================================"
echo "  Done! Restart Django."
echo "  sync_engine.py is untouched."
echo "========================================"
