from django.db import models, transaction
from django.db.models import F, Max
from django.db.models.signals import post_save
from django.dispatch import receiver
from product.models import Product, ProductCategory, ProductChildVariant
from django.core.exceptions import ObjectDoesNotExist
from user.models import User

class UserPreferences(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    preference = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, null=True)

class UserPreferencesCount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    count = models.PositiveBigIntegerField()

@receiver(post_save, sender=UserPreferencesCount)
def update_user_preferences(sender, instance, **kwargs):
    user_id = instance.user_id
    
    # Get the category with the highest count for the user
    try:
        highest_count_category = (
            UserPreferencesCount.objects
            .filter(user_id=user_id)
            .values('category')
            .annotate(max_count=Max('count'))
            .order_by('-max_count')
            .first()
        )
    except ObjectDoesNotExist:
        highest_count_category = None
    
    if highest_count_category:
        category_id = highest_count_category['category']
        
        # Update or create UserPreferences record
        with transaction.atomic():
            user_preference, created = UserPreferences.objects.get_or_create(user_id=user_id)
            user_preference.preference_id = category_id
            user_preference.save()
    else:
        # If there are no categories for the user, set preference to None
        UserPreferences.objects.filter(user_id=user_id).update(preference_id=None)

class UserHistory(models.Model):
    user = models.ForeignKey(User,on_delete = models.CASCADE)
    product = models.ForeignKey(Product, on_delete = models.CASCADE)
    checked_at = models.DateTimeField(auto_now_add=True)

class Referral(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    referral_code = models.CharField(max_length = 50)


class ReferralCodeHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_codes_given')
    referral_rewards = models.DecimalField(decimal_places=2, max_digits=10, null=True, default=0)
    new_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referral_code_received')
    joining_rewards = models.DecimalField(decimal_places=2, max_digits=10, null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    

class ReferralRewardSchemes(models.Model):
    joining = models.DecimalField(decimal_places=2, max_digits=10, null=True, default=0)
    referral = models.DecimalField(decimal_places=2, max_digits=10, null=True, default=0)
    status = models.BooleanField(default=False)


class Banner(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='banners/')
    text = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    reference = models.ForeignKey(Product,  on_delete = models.CASCADE)

    def __str__(self):
        return self.title

    










    