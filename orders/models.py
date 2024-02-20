from django.db import models
from django.core.exceptions import ValidationError
from user.models import User
from product.models import Product, ProductChildVariant

# Create your models here.

class Cart(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    child_variant =models.ForeignKey(ProductChildVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)
    class Meta:
        unique_together = ('user', 'child_variant')


class Coupon(models.Model):
    code = models.CharField(max_length=100, help_text="Coupon code")
    
    DISCOUNT_TYPE_CHOICES = (
        ('%', 'Percentage'),
        ('$', 'Cash'),
    )
    coupon_type = models.CharField(max_length=1, choices=DISCOUNT_TYPE_CHOICES, help_text="Type of discount")
    
    coupon_value = models.PositiveBigIntegerField(help_text="Discount value")
    min_order = models.PositiveBigIntegerField(null=True, blank=True, help_text="Minimum order amount for the coupon to be valid")
    max_user = models.PositiveBigIntegerField(help_text="Maximum number of users who can use the coupon")
    count = models.PositiveBigIntegerField(default = 0)
    exp_date = models.DateField(help_text="Expiration date of the coupon")    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def clean(self):
        if self.coupon_type == '%':
            if self.coupon_value <= 0 or self.coupon_value > 90:
                raise ValidationError("Percentage discount value must be between 1% and 90%.")
            
        elif self.coupon_type == '$':
            if self.coupon_value < 0:
                raise ValidationError("Fixed amount discount value cannot be negative.")
            
            if self.min_order is not None and (self.min_order < 0 or self.min_order <= self.coupon_value):
                raise ValidationError("Minimum order must be greater than 0 and greater than the discount value for fixed amount discounts.")
        else:
            raise ValidationError("Invalid coupon type.")
        

    

class AppliedCoupon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    successfully_applied = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.coupon.code} (Applied: {self.successfully_applied})"



