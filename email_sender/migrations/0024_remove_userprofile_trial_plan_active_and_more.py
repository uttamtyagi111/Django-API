# Generated by Django 5.1.2 on 2024-10-23 20:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_sender', '0023_rename_plan_expiry_date_userprofile_plan_expiration_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='trial_plan_active',
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='emails_sent',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='plan_status',
            field=models.CharField(default='active', max_length=20),
        ),
    ]
