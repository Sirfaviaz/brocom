# Generated by Django 4.2.7 on 2024-01-16 04:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0011_productvariant_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariantinfo',
            name='price',
            field=models.PositiveBigIntegerField(null=True),
        ),
    ]
