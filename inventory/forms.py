from django import forms
from .models import Urun


class UrunForm(forms.ModelForm):
    barkod_no = forms.CharField(
        required=False,
        label="Barkod Numarası (opsiyonel)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Urun
        fields = ['ad', 'kategori', 'alis_fiyati', 'satis_fiyati', 'stok_miktari', 'kritik_stok_seviyesi']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control'}),
            'kategori': forms.Select(attrs={'class': 'form-select'}),
            'alis_fiyati': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'satis_fiyati': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stok_miktari': forms.NumberInput(attrs={'class': 'form-control'}),
            'kritik_stok_seviyesi': forms.NumberInput(attrs={'class': 'form-control'}),
        }