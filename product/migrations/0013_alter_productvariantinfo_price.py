# Generated by Django 4.2.7 on 2024-01-16 04:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0012_productvariantinfo_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productvariantinfo',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
    ]
