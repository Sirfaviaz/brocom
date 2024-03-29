# Generated by Django 4.2.7 on 2024-01-17 07:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0016_alter_productinventory_quantity'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productinventory',
            name='description',
        ),
        migrations.RemoveField(
            model_name='productinventory',
            name='has_variants',
        ),
        migrations.RemoveField(
            model_name='productinventory',
            name='quantity',
        ),
        migrations.RemoveField(
            model_name='productinventory',
            name='status',
        ),
        migrations.RemoveField(
            model_name='productinventory',
            name='supplier_id',
        ),
        migrations.RemoveField(
            model_name='productvariantinventory',
            name='name',
        ),
        migrations.AddField(
            model_name='productvariantinventory',
            name='size',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='productvariantinventory',
            name='inventory',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', related_query_name='variants_inventory', to='product.productinventory'),
        ),
    ]
