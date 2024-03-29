# Generated by Django 4.2.7 on 2023-12-17 11:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0007_alter_user_firstname_alter_user_lastname'),
        ('orders', '0002_cart_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='Coupon code', max_length=100)),
                ('coupon_type', models.CharField(choices=[('%', 'Percentage'), ('$', 'Cash')], help_text='Type of discount', max_length=1)),
                ('coupon_value', models.PositiveBigIntegerField(help_text='Discount value')),
                ('min_order', models.PositiveBigIntegerField(blank=True, help_text='Minimum order amount for the coupon to be valid', null=True)),
                ('max_user', models.PositiveBigIntegerField(help_text='Maximum number of users who can use the coupon')),
                ('count', models.PositiveBigIntegerField()),
                ('exp_date', models.DateField(help_text='Expiration date of the coupon')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='AppliedCoupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('successfully_applied', models.BooleanField(default=False)),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='orders.coupon')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.user')),
            ],
        ),
    ]
