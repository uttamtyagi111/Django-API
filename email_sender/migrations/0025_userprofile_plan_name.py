# Generated by Django 5.1.2 on 2024-10-24 00:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_sender', '0024_remove_userprofile_trial_plan_active_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='plan_name',
            field=models.CharField(default='Trial', max_length=20),
        ),
    ]
