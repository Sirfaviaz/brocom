# Generated by Django 4.2.7 on 2024-01-14 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_alter_coupon_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='variant',
            field=models.PositiveBigIntegerField(default=None, null=True),
        ),
    ]
