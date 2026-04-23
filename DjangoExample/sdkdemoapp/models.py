import secrets
from django.db import models
from django.utils import timezone

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
            models.UniqueConstraint(name="device_log_id", fields=["device_id", "log_id"])
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


class Zone(models.Model):
    """Physical zone/area that devices can be assigned to."""
    name        = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True, default='')
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class DeviceRegistry(models.Model):
    """Persistent record of a known device."""
    serial_number   = models.CharField(max_length=256, unique=True)
    friendly_name   = models.CharField(max_length=256, blank=True, default='')
    zone            = models.ForeignKey(Zone, null=True, blank=True, on_delete=models.SET_NULL, related_name='devices')
    location        = models.CharField(max_length=256, blank=True, default='')
    terminal_type   = models.CharField(max_length=128, blank=True, default='')
    product_name    = models.CharField(max_length=128, blank=True, default='')
    is_active       = models.BooleanField(default=True)
    interlock_enabled = models.BooleanField(default=False)
    registered_at   = models.DateTimeField(auto_now_add=True)
    last_seen       = models.DateTimeField(null=True, blank=True)
    token           = models.CharField(max_length=64, blank=True, default='')

    def __str__(self):
        return self.friendly_name or self.serial_number

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(16)
        super().save(*args, **kwargs)


class DeviceConnectionLog(models.Model):
    """Log of device connect/disconnect events."""
    CONNECT    = 'connect'
    DISCONNECT = 'disconnect'
    EVENT_CHOICES = [(CONNECT, 'Connected'), (DISCONNECT, 'Disconnected')]

    device_id   = models.CharField(max_length=256)
    event       = models.CharField(max_length=16, choices=EVENT_CHOICES)
    timestamp   = models.DateTimeField(default=timezone.now)
    ip_address  = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        ordering = ['-timestamp']


class Employee(models.Model):
    """Local employee record — synced to devices automatically on save."""
    employee_id     = models.IntegerField(unique=True)
    name            = models.CharField(max_length=256)
    department      = models.IntegerField(default=0)
    privilege       = models.IntegerField(default=0)
    enabled         = models.BooleanField(default=True)
    card            = models.CharField(max_length=128, blank=True, null=True)
    password        = models.CharField(max_length=128, blank=True, null=True)
    period_start    = models.DateField(null=True, blank=True)
    period_end      = models.DateField(null=True, blank=True)
    timeset_1       = models.IntegerField(default=-1)
    timeset_2       = models.IntegerField(default=-1)
    timeset_3       = models.IntegerField(default=-1)
    timeset_4       = models.IntegerField(default=-1)
    timeset_5       = models.IntegerField(default=-1)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee_id} - {self.name}"


class InterlockState(models.Model):
    """Tracks which employee last punched in, used for interlock logic."""
    employee_id     = models.IntegerField(unique=True)
    punched_device  = models.CharField(max_length=256)
    punch_time      = models.DateTimeField(default=timezone.now)
    interlock_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-punch_time']


class APIKey(models.Model):
    """API key for third-party software integration."""
    name        = models.CharField(max_length=128)
    key         = models.CharField(max_length=64, unique=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    last_used   = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_hex(32)
        super().save(*args, **kwargs)
