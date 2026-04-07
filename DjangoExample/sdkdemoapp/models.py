from django.db import models

# Create your models here.
class FirmwareBinary(models.Model):
    name    = models.CharField(max_length = 256, primary_key = True, unique = True)
    data    = models.BinaryField()

class AttendanceLog(models.Model):
    device_id           = models.CharField(max_length = 256, null = False)
    log_id              = models.IntegerField(blank = False, null = False)
    time                = models.DateTimeField(blank = True, null = True)
    user_id             = models.IntegerField(blank = True, null = True)
    timezone_offset     = models.IntegerField(blank = True, null = True)
    attend_status       = models.CharField(max_length = 256, blank = True, null = True)
    action              = models.CharField(max_length = 256, blank = True, null = True)
    job_code            = models.IntegerField(blank = True, null = True)
    photo               = models.BinaryField(blank = True, null = True)
    body_temperature    = models.IntegerField(blank = True, null = True)
    attend_only         = models.BooleanField(blank = False, null = False)
    expired             = models.BooleanField(blank = False, null = False)
    latitude            = models.CharField(max_length = 256, blank = True, null = True)
    longitude           = models.CharField(max_length = 256, blank = True, null = True)

    class Meta:
        constraints = [
            models.UniqueConstraint(name="device_log_id", fields=["device_id", "log_id"], nulls_distinct=False)
        ]

class ManagementLog(models.Model):
    device_id           = models.CharField(max_length = 256, null = False)
    log_id              = models.IntegerField(blank = False, null = False)
    time                = models.DateTimeField(blank = True, null = True)
    admin_id            = models.IntegerField(blank = True, null = True)
    employee_id         = models.IntegerField(blank = True, null = True)
    action              = models.CharField(max_length = 256, blank = True, null = True)
    result              = models.IntegerField(blank = True, null = True)


class OEMSettings(models.Model):
    """Singleton model — always use pk=1. Stores white-label branding."""
    app_name        = models.CharField(max_length=128, default='Web SDK Demo App')
    company_name    = models.CharField(max_length=128, default='', blank=True)
    navbar_color    = models.CharField(max_length=32,  default='#ffffff')
    navbar_text_color = models.CharField(max_length=32, default='#212529')
    primary_color   = models.CharField(max_length=32,  default='#0d6efd')
    logo_url        = models.CharField(max_length=512, default='', blank=True)
    footer_text     = models.CharField(max_length=256, default='© 2025')

    class Meta:
        verbose_name = 'OEM Settings'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
