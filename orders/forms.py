from django import forms
from .models import Coupon

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'coupon_type', 'coupon_value', 'min_order', 'max_user', 'count', 'exp_date']
        widgets = {
            'exp_date': forms.DateInput(attrs={'type': 'date'}),
        }