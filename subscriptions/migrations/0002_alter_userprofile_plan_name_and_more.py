# Generated by Django 5.1.2 on 2024-11-05 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='plan_name',
            field=models.CharField(choices=[('Trial', 'Trial'), ('Basic', 'Basic'), ('Premium', 'Premium')], default='Trial', max_length=20),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='plan_status',
            field=models.CharField(default='trial', max_length=20),
        ),
    ]