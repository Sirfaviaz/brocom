# Generated by Django 4.2.7 on 2023-12-30 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0016_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitems',
            name='delivery',
            field=models.CharField(choices=[('Pending', 'pending'), ('Delivered', 'delivered'), ('Cancelled', 'cancelled')], default='Pending', max_length=10),
        ),
    ]
