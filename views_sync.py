"""
sync_views.py — Django view for the Sync Users page
=====================================================
Drop this into: DjangoExample/sdkdemoapp/views_sync.py

Then in urls.py add:
    from sdkdemoapp.views_sync import sync_users_view
    path('sync_users', sync_users_view, name='sync_users'),
"""

from django.shortcuts import render
from django.http import HttpResponse

from sdkdemoapp.biz import devices as devices_biz
from sdkdemoapp.biz.sync_users_biz import run_sync


def sync_users_view(request):
    """
    GET  → Show device list with host/target selection
    POST → Run the sync and display log output
    """
    # Get list of online devices
    try:
        online_devices = devices_biz.get_all()
    except Exception:
        online_devices = []

    context = {
        "devices": online_devices,
        "sync_log": None,
        "error": None,
    }

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "sync":
            host_cid_str = request.POST.get("host", "")
            target_cids_str = request.POST.getlist("targets")

            # Validate
            if not host_cid_str:
                context["error"] = "Please select a host device."
                return render(request, "sdkdemoapp/sync_users.html", context)

            if not target_cids_str:
                context["error"] = "Please select at least one target device."
                return render(request, "sdkdemoapp/sync_users.html", context)

            try:
                host_cid = int(host_cid_str)
                target_cids = [int(x) for x in target_cids_str]
            except ValueError:
                context["error"] = "Invalid device ID."
                return render(request, "sdkdemoapp/sync_users.html", context)

            # Don't allow host as target
            target_cids = [t for t in target_cids if t != host_cid]
            if not target_cids:
                context["error"] = "Target device cannot be the same as host."
                return render(request, "sdkdemoapp/sync_users.html", context)

            # Run sync
            try:
                log_lines = run_sync(host_cid, target_cids)
                context["sync_log"] = "\n".join(log_lines)
            except Exception as exc:
                context["error"] = f"Sync failed: {exc}"

    return render(request, "sdkdemoapp/sync_users.html", context)
