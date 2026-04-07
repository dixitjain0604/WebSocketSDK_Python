from .models import OEMSettings


def oem(request):
    return {'oem': OEMSettings.get()}
