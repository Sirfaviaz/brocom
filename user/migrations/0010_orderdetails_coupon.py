# Generated by Django 4.2.7 on 2023-12-25 05:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0009_wallettranslation_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdetails',
            name='coupon',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
