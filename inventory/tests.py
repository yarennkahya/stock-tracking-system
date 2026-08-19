from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import Firma, Senet
from .forms import UrunForm
from .models import Barkod, Kategori, Urun


class HizliUrunEklemeTestleri(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('depo', 'depo@example.com', 'GucluSifre123!')
        self.client.force_login(self.user)
        ana_kategori = Kategori.objects.create(ad='Boru ve ek parçaları')
        self.kategori = Kategori.objects.create(ad='PVC ek parçaları', parent=ana_kategori)

    def test_barkodla_yeni_urun_kaydedilir(self):
        response = self.client.post(
            reverse('hizli_urun_kaydet'),
            {
                'barkod_no': '8699876543210', 'ad': 'PVC Dirsek 50 mm', 'kategori_id': self.kategori.id,
                'alis_fiyati': '14.50', 'satis_fiyati': '22.00', 'stok_miktari': '12',
            },
        )

        self.assertEqual(response.status_code, 200)
        urun = Urun.objects.get(ad='PVC Dirsek 50 mm')
        self.assertEqual(urun.stok_miktari, 12)
        self.assertTrue(Barkod.objects.filter(urun=urun, barkod_no='8699876543210').exists())

    def test_barkodsuz_urun_de_kaydedilebilir(self):
        response = self.client.post(
            reverse('hizli_urun_kaydet'),
            {
                'barkod_no': '', 'ad': 'Teflon Bant', 'kategori_id': self.kategori.id,
                'alis_fiyati': '5.00', 'satis_fiyati': '9.00', 'stok_miktari': '20',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Urun.objects.filter(ad='Teflon Bant').exists())

    def test_alt_kategoriler_api_ana_kategoriye_gore_filtrelenir(self):
        response = self.client.get(reverse('alt_kategoriler', args=[self.kategori.parent_id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['alt_kategoriler'], [{'id': self.kategori.id, 'ad': 'PVC ek parçaları'}])

    def test_kategori_ekranindan_alt_kategori_eklenebilir(self):
        response = self.client.post(
            reverse('kategori_listesi'),
            {'ad': 'PPRC ek parçaları', 'parent': self.kategori.parent_id, 'aciklama': ''},
        )

        self.assertRedirects(response, reverse('kategori_listesi'))
        self.assertTrue(Kategori.objects.filter(ad='PPRC ek parçaları', parent=self.kategori.parent).exists())

    def test_fiyat_adimi_bir_tldir(self):
        form = UrunForm()

        self.assertEqual(form.fields['alis_fiyati'].widget.attrs['step'], '1')
        self.assertEqual(form.fields['satis_fiyati'].widget.attrs['step'], '1')

    def test_demo_veri_komutu_kategori_urun_firma_ve_senet_ekler(self):
        call_command('seed_demo_verileri')

        self.assertTrue(Kategori.objects.filter(ad='Vitrifiye', parent__isnull=True).exists())
        self.assertTrue(Urun.objects.filter(ad='Seramik Klozet Takımı').exists())
        self.assertTrue(Firma.objects.filter(ad='Demo Tesisat Tedarik').exists())
        self.assertEqual(Senet.objects.filter(firma__ad='Demo Tesisat Tedarik', durum='bekliyor').count(), 2)
