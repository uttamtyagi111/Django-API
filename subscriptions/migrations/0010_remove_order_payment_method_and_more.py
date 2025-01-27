# Generated by Django 5.1.2 on 2024-11-11 15:52

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0009_alter_userprofile_plan_expiration_date_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='payment_method',
        ),
        migrations.RemoveField(
            model_name='order',
            name='transaction_id',
        ),
        migrations.AddField(
            model_name='order',
            name='razorpay_payment_id',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='plan_expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 12, 11, 15, 52, 9, 890829, tzinfo=datetime.timezone.utc)),
        ),
    ]
