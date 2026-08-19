from django import forms
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import Firma, Senet


class UyeOlFormu(UserCreationForm):
    email = forms.EmailField(label='E-posta adresi', required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        labels = {
            'username': 'Kullanıcı adı',
            'password1': 'Şifre',
            'password2': 'Şifre tekrarı',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Bu e-posta adresi zaten kullanılıyor.')
        return email


class SifreSifirlamaFormu(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['placeholder'] = 'ornek@eposta.com'


class HesapAyarlariFormu(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {
            'username': _('Kullanıcı adı'),
            'first_name': _('Ad'),
            'last_name': _('Soyad'),
            'email': _('E-posta adresi'),
        }
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'username'}),
            'first_name': forms.TextInput(attrs={'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('Bu e-posta adresi başka bir hesap tarafından kullanılıyor.'))
        return email


class FirmaFormu(forms.ModelForm):
    class Meta:
        model = Firma
        fields = ('ad', 'telefon', 'adres')
        labels = {'ad': 'Firma adı', 'telefon': 'Telefon', 'adres': 'Adres'}
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn. ABC Tesisat Ltd.'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn. 0532 000 00 00'}),
            'adres': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SenetFormu(forms.ModelForm):
    class Meta:
        model = Senet
        fields = ('firma', 'tip', 'tutar', 'vade_tarihi', 'durum', 'aciklama')
        labels = {
            'firma': 'Firma', 'tip': 'Senet tipi', 'tutar': 'Tutar',
            'vade_tarihi': 'Vade tarihi', 'durum': 'Durum', 'aciklama': 'Açıklama',
        }
        widgets = {
            'firma': forms.Select(attrs={'class': 'form-select'}),
            'tip': forms.Select(attrs={'class': 'form-select'}),
            'tutar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'vade_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'durum': forms.Select(attrs={'class': 'form-select'}),
            'aciklama': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn. 2. taksit'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['firma'].queryset = Firma.objects.order_by('ad')
