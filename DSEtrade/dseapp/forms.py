from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['instrument', 'quantity', 'cost_price']
        widgets = {
            'instrument': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter instrument name'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter quantity'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-input pl-12',
                'placeholder': 'Enter cost price',
                'step': '0.01'
            }),
        }