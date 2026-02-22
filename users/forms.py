from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Подтвердите пароль",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ["email", "full_name", "phone"]
        labels = {
            "email": "Email",
            "full_name": "ФИО",
            "phone": "Телефон",
        }

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Пароли не совпадают.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user




class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["full_name", "phone", "email"]
        labels = {
            "full_name": "ФИО",
            "phone": "Телефон",
            "email": "Email",
        }