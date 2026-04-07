from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sdkdemoapp', '0003_managementlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='OEMSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app_name',          models.CharField(default='Web SDK Demo App', max_length=128)),
                ('company_name',      models.CharField(blank=True, default='', max_length=128)),
                ('navbar_color',      models.CharField(default='#ffffff', max_length=32)),
                ('navbar_text_color', models.CharField(default='#212529', max_length=32)),
                ('primary_color',     models.CharField(default='#0d6efd', max_length=32)),
                ('logo_url',          models.CharField(blank=True, default='', max_length=512)),
                ('footer_text',       models.CharField(default='© 2025', max_length=256)),
            ],
            options={
                'verbose_name': 'OEM Settings',
            },
        ),
    ]
