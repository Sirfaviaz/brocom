# Generated by Django 4.2.7 on 2024-01-15 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0010_alter_productvariant_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariant',
            name='name',
            field=models.CharField(max_length=10, null=True),
        ),
    ]
