# Generated by Django 4.2.7 on 2024-01-29 07:59

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('cadmin', '0004_referralrewardschemes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='referralcodehistory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
