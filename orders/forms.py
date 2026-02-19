from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['name', 'phone', 'email', 'address', 'comment']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 4}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            self.fields['email'].initial = user.email
