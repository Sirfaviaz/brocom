from colorfield.fields import ColorField
from django.utils import timezone
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError



# Create your models here.
class ProductInventory(models.Model):
    name = models.CharField(max_length=50)
    has_variants = models.BooleanField(null = True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
class ProductParentVariantInventory(models.Model):
    inventory = models.ForeignKey(ProductInventory, on_delete=models.CASCADE, related_name='variants',related_query_name='variants_inventory')
    color = models.CharField(max_length=50 ,null = True)
   
    def all_child_variants(self):
        return ProductChildVariantInventory.objects.filter(parent_variant=self)
    
class ProductChildVariantInventory(models.Model):
    parent_variant = models.ForeignKey(ProductParentVariantInventory,on_delete = models.CASCADE,related_name='parent_variant' )
    size = models.CharField(max_length=50, null=True)
    quantity = models.PositiveIntegerField()
    supplier_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10)
    







class Discount(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=100,null=True)
    is_percentage = models.BooleanField(default=True)
    disc_value = models.DecimalField(max_digits=10,decimal_places=2)
    isactive = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class ProductCategory(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10)
    discount = models.ForeignKey(Discount, null=True, on_delete=models.CASCADE, default=None)
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=50)
    inventory = models.ForeignKey(ProductInventory, on_delete = models.CASCADE, null = True)
    description = models.TextField()
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)    
    status = models.CharField(max_length=10, default='active')
    has_variants = models.BooleanField(default=False)
    discount = models.ForeignKey(Discount, null = True, on_delete = models.CASCADE)

    
    def __str__(self):
        return self.name
    def get_smallest_price(self):
        child_variants = ProductChildVariant.objects.filter(parent_variant__product=self)
        if child_variants.exists():
            return min(child_variants.values_list('price', flat=True))
        return None
    def get_default_product(self):
        default_products = ProductParentVariant.objects.get(product=self, default = True)
       
        return default_products
        
            

       


class ProductParentVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='color', related_query_name='color')
    inventory_parent = models.ForeignKey(ProductParentVariantInventory, on_delete=models.CASCADE, related_name='inv_parent', related_query_name='inv_parent')
    color = ColorField()
    main_image = models.ImageField(upload_to='product_images/')
    default = models.BooleanField(default=False, null=True)
    discount = models.ForeignKey(Discount, null = True, on_delete = models.CASCADE)

    def save(self, *args, **kwargs):
        if self.default:
            # Set default to False for other instances of the same product
            ProductParentVariant.objects.filter(product=self.product).exclude(id=self.id).update(default=False)
        else:
            # If none are set as default, set the last entry as default
            if not ProductParentVariant.objects.filter(product=self.product, default=True).exists():
                latest_variant = ProductParentVariant.objects.filter(product=self.product).order_by('-id').first()
                if latest_variant:
                    latest_variant.default = True
                    latest_variant.save()

        super(ProductParentVariant, self).save(*args, **kwargs)

# Signal to ensure only one instance has default set to True for each product
@receiver(post_save, sender=ProductParentVariant)
def ensure_single_default(sender, instance, **kwargs):
    if instance.default:
        ProductParentVariant.objects.filter(product=instance.product).exclude(id=instance.id).update(default=False)


class ProductChildVariant(models.Model):
    parent_variant = models.ForeignKey(ProductParentVariant, on_delete=models.CASCADE, related_name='parent', related_query_name='parent')
    inventory_child = models.ForeignKey(ProductChildVariantInventory, on_delete=models.CASCADE, related_name='inv_child', related_query_name='inv_child')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.ForeignKey(Discount, null = True, on_delete = models.CASCADE)

    def clean(self):
        if self.price < 0:
            raise ValidationError("Price must be a non-negative value.")
        # You can add more validation logic as needed

    def save(self, *args, **kwargs):
        self.clean()  # Run validation before saving
        super().save(*args, **kwargs)
   

class ProductVariantColorImages(models.Model):
    parent_variant= models.ForeignKey(ProductParentVariant, on_delete=models.CASCADE, related_name='images', related_query_name='image')
    image = models.ImageField(upload_to='variant_product_images/')
    created_at = models.DateTimeField(auto_now_add=True, null = True)
    modified_at = models.DateTimeField(auto_now=True, null = True)

    class Meta:
        ordering = ['parent_variant_id']



    
   









# @receiver(post_save, sender=ProductVariant)
# def update_inventory_quantity(sender, instance, **kwargs):
#         product = instance.product
#         variants = ProductVariant.objects.filter(product=product)
#         total_quantity = variants.aggregate(models.Sum('quantity'))['quantity__sum'] or 0
#         product.inventory.quantity = total_quantity
#         product.inventory.save()

# # Connect the signal
# post_save.connect(update_inventory_quantity, sender=ProductVariant)
    

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, default='active')
    def __str__(self):
        return self.name


class ProductRating(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comments = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
       
        unique_together = ('user', 'product')

