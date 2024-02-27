from datetime import timedelta
from django.utils import timezone
from decimal import Decimal
from django.db import models
from product.models import Product, ProductChildVariant
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone




# Create your models here.
class User(models.Model):
    username = models.CharField(max_length=100)
    firstname = models.TextField()
    lastname = models.TextField()
    email = models.EmailField()
    mobile = PhoneNumberField()
    password = models.CharField(max_length=128)
    joined_on = models.DateTimeField(auto_now_add =True)
    last_activity = models.DateField(auto_now = True)
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    birthday = models.DateField()
    verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default= 'active')
    adminstatus = models.CharField(max_length = 10, default= 'user')


    def __str__(self) -> str:
        return self.username
    
class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE )
    Name = models.TextField()
    address_line_1 = models.TextField()
    address_line_2 = models.TextField()
    pincode = models.PositiveBigIntegerField()
    city = models.CharField(max_length=100, verbose_name=_("City"))
    state = models.CharField(max_length=100, verbose_name=_("State"))
    
    country = models.CharField(max_length=100, verbose_name=_("Country"))
    mobile = PhoneNumberField()
    is_default = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user.username} - {self.address_line_1}, {self.city}, {self.country}, {self.state}"





class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))
    def clean(self):
        if self.balance < 0:
            raise ValidationError("Balance cannot be negative.")
        super().clean()
    
    @transaction.atomic
    def deposit(self, amount):
        self.balance += amount
        self.save()
        BalanceChange.objects.create(wallet=self, amount=amount)

    @transaction.atomic
    def withdraw(self, amount):
        try:
            if amount <= self.balance:
                self.balance -= amount
                
                self.save()
                BalanceChange.objects.create(wallet=self, amount=-amount)
            else:
                raise ValueError(f"Insufficient funds for withdrawal from {self.user.username}'s wallet.")
        except ValueError as e:
            return str(e)
    
    def __str__(self):
        return f"{self.user.username}'s Wallet - Balance: {self.balance}"
    
class BalanceChange(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

# @receiver(post_save, sender=Wallet)
# def log_balance_change(sender, instance, **kwargs):
#         print("Signal is working!")
#         if kwargs['created']:
#             return  

#         old_balance = Wallet.objects.get(pk=instance.pk).balance
#         if old_balance != instance.balance:
#             BalanceChange.objects.create(wallet=instance, amount=instance.balance - old_balance)

    

class WalletTranslation(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete = models.CASCADE)
    TYPE_CHOICES = (
        ('p', 'paid'),
        ('r', 'Received'),
        
    )
    type = models.CharField(max_length = 1, choices =  TYPE_CHOICES)
    date = models.DateTimeField(auto_now_add = True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, default = 0)
    naration = models.TextField() 

    def __str__(self):

        return f"{self.get_type_display()} Transaction on {self.date} - {self.naration}"

class PaymentMethod(models.TextChoices):
    RAZORPAY = 'Razorpay', 'razorpay'
    WALLET = 'Wallet', 'wallet'    

class PaymentDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices)
    additional_payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, blank=True, null=True)
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.payment_method} - {self.created_on}"


class OrderDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment = models.ForeignKey(PaymentDetails, on_delete=models.CASCADE)
    coupon = models.CharField(max_length = 50, blank=True, null=True )
  
    address = models.IntegerField(default = 0)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length = 10, blank=True, null=True )


    def __str__(self):
        return f"{self.user} - {self.amount} - {self.created_at}"
def get_default_date():
        return timezone.now()
def get_rounded_date(self):
        return self.created_at.replace(minute=0, second=0, microsecond=0) + timedelta(hours=4)

class OrderItems(models.Model):
    order = models.ForeignKey(OrderDetails, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductChildVariant, on_delete=models.CASCADE)
    quantity = models.PositiveBigIntegerField()
    amount = models.PositiveBigIntegerField(default = 0)
    created_at = models.DateTimeField(auto_now_add=True)    
    STATUS_CHOICES = (
        
        ('Return', 'Return'),
        ('Cancel', 'Cancel'),

    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES,blank=True, null=True )
    REQUEST_CHOICES = (
        
        ('Cancel', 'Cancel'),
        ('Approve', 'Approve'),

    )
    
    refund = models.CharField(max_length = 10, choices = REQUEST_CHOICES, blank=True, null=True)
    DELIVERY_CHOICES = (
        
        ('Pending', 'pending'),
        ('Delivered', 'delivered'),
        ('Cancelled','cancelled')

    )
    delivery = models.CharField(max_length = 10, choices = DELIVERY_CHOICES, default = 'Pending' )
    modified_at = models.DateTimeField(auto_now=True)

  

    def __str__(self):
        return f"{self.order} - {self.product} - {self.quantity} - {self.created_at}"
    

class Order(models.Model):
    order_id = models.CharField(max_length=255)
    amount = models.FloatField()
    status = models.CharField(max_length=20, default='pending')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    Address_id = models.IntegerField(blank=True,default = 0)
    coupon_code = models.CharField(max_length = 10, blank=True, null=True )

class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_items = models.ForeignKey(OrderItems,on_delete=models.CASCADE)
    total_amount = models.PositiveBigIntegerField()
    invoice_date = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Invoice for {self.user.username} - {self.invoice_date}"







