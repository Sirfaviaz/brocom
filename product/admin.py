from django.contrib import admin
from .models import Product, ProductCategory, ProductInventory, Discount, Supplier,ProductParentVariant,ProductVariantColorImages,ProductChildVariant
# Register your models here.
admin.site.register(Product)

admin.site.register(ProductInventory)
admin.site.register(ProductCategory)
admin.site.register(Discount)

admin.site.register(Supplier)
admin.site.register(ProductChildVariant)
admin.site.register(ProductParentVariant)
admin.site.register(ProductVariantColorImages)