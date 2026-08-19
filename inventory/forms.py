from django import forms
from .models import Kategori, Urun


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
            'alis_fiyati': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'}),
            'satis_fiyati': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'}),
            'stok_miktari': forms.NumberInput(attrs={'class': 'form-control'}),
            'kritik_stok_seviyesi': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['kategori'].queryset = Kategori.objects.filter(parent__isnull=False).select_related('parent')
        self.fields['kategori'].label_from_instance = lambda kategori: kategori.tam_ad


class KategoriFormu(forms.ModelForm):
    class Meta:
        model = Kategori
        fields = ('ad', 'parent', 'aciklama')
        labels = {'ad': 'Kategori adı', 'parent': 'Ana kategori', 'aciklama': 'Açıklama'}
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn. PVC Boru ve Ek Parçaları'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = Kategori.objects.filter(parent__isnull=True)
        self.fields['parent'].empty_label = 'Ana kategori olarak ekle'
