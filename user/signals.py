from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver
from user.models import Wallet, BalanceChange

@receiver(post_save, sender=Wallet)
def log_balance_change(sender, instance, **kwargs):
    if kwargs['created']:
        return

    old_balance = Wallet.objects.get(pk=instance.pk).balance
    if old_balance != instance.balance:
        BalanceChange.objects.create(wallet=instance, amount=instance.balance - old_balance)