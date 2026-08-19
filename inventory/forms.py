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

        if self.instance and self.instance.pk and 'barkod_no' not in self.initial:
            mevcut_barkod = self.instance.barkodlar.order_by('id').first()
            if mevcut_barkod:
                self.initial['barkod_no'] = mevcut_barkod.barkod_no

    def clean_barkod_no(self):
        barkod_no = self.cleaned_data['barkod_no'].strip()
        if not barkod_no:
            return barkod_no

        from .models import Barkod

        mevcut_barkodlar = Barkod.objects.filter(barkod_no=barkod_no)
        if self.instance and self.instance.pk:
            mevcut_barkodlar = mevcut_barkodlar.exclude(urun=self.instance)
        if mevcut_barkodlar.exists():
            raise forms.ValidationError('Bu barkod başka bir üründe kayıtlı.')
        return barkod_no


class AltKategoriFormu(forms.ModelForm):
    class Meta:
        model = Kategori
        fields = ('ad', 'aciklama')
        labels = {'ad': 'Alt kategori adı', 'aciklama': 'Açıklama'}
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn. PVC ek parçaları'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
