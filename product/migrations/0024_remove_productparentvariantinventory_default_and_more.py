# Generated by Django 4.2.7 on 2024-01-20 06:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0023_alter_productchildvariant_inventory_child_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productparentvariantinventory',
            name='default',
        ),
        migrations.AddField(
            model_name='productparentvariant',
            name='default',
            field=models.CharField(max_length=10, null=True),
        ),
    ]
