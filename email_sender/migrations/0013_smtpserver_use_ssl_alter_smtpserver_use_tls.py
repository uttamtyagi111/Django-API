# Generated by Django 5.1 on 2024-10-05 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_sender', '0012_delete_sender'),
    ]

    operations = [
        migrations.AddField(
            model_name='smtpserver',
            name='use_ssl',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='smtpserver',
            name='use_tls',
            field=models.BooleanField(default=True),
        ),
    ]
