from django import forms
from colorfield.fields import ColorField
from django.core import validators

class MultipleFileInput(forms.FileInput):
    allow_multiple = True

    def render(self, name, value, attrs=None, renderer=None):
        attrs['multiple'] = 'multiple'
        return super().render(name, value, attrs, renderer)

class ProductVariantForm(forms.Form):
    inventory_id = forms.IntegerField(widget=forms.HiddenInput)
    color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'type':'text'}))
    images = forms.FileField(widget=MultipleFileInput(attrs={'accept': 'image/*'}),
                             validators=[validators.validate_image_file_extension])
    
class AddFieldForm(forms.Form):
    size = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'type': 'text'}))
    quantity = forms.IntegerField(required=True, widget=forms.TextInput(attrs={'type': 'number'}))
    price = forms.DecimalField(required=True, max_digits=10, decimal_places=2, widget=forms.TextInput(attrs={'type': 'number'}))

    def clean_size(self):
        size = self.cleaned_data.get('size')
        if ' ' in size:
            raise forms.ValidationError("Size should not contain spaces.")
        return size

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError("Quantity should be a positive integer.")
        return quantity

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError("Price should be a non-negative number.")
        return price