# Generated by Django 4.2.7 on 2024-01-07 21:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0018_orderdetails_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='Address_id',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='order',
            name='coupon_code',
            field=models.TextField(blank=True, default=0),
        ),
    ]
