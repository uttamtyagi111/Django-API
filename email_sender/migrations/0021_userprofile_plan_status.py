# Generated by Django 5.1.2 on 2024-10-23 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_sender', '0020_userprofile_trial_plan_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='plan_status',
            field=models.CharField(default='inactive', max_length=50),
        ),
    ]
