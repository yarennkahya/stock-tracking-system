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
            {'ad': 'PPRC ek parçaları', 'ana_kategori': self.kategori.parent_id, 'aciklama': ''},
        )

        self.assertRedirects(response, f"{reverse('kategori_listesi')}?ana_kategori={self.kategori.parent_id}")
        self.assertTrue(Kategori.objects.filter(ad='PPRC ek parçaları', parent=self.kategori.parent).exists())

    def test_kategori_ekrani_ana_kategori_secmeden_alt_kategori_formunu_gostermez(self):
        response = self.client.get(reverse('kategori_listesi'))

        self.assertContains(response, 'Bir ana kategori seçin')
        self.assertNotContains(response, 'Alt kategoriyi kaydet')

    def test_urun_listesi_ana_alt_kategori_ve_barkoda_gore_filtrelenir(self):
        urun = Urun.objects.create(
            ad='PVC Dirsek', kategori=self.kategori, alis_fiyati='10.00', satis_fiyati='15.00', stok_miktari=12,
        )
        Barkod.objects.create(urun=urun, barkod_no='8691112223334')
        diger_ana_kategori = Kategori.objects.create(ad='Vitrifiye')
        diger_alt_kategori = Kategori.objects.create(ad='Klozet', parent=diger_ana_kategori)
        Urun.objects.create(
            ad='Seramik Klozet', kategori=diger_alt_kategori, alis_fiyati='100.00', satis_fiyati='150.00', stok_miktari=8,
        )

        ana_kategori_response = self.client.get(reverse('ana_sayfa'), {'ana_kategori': self.kategori.parent_id})
        barkod_response = self.client.get(reverse('ana_sayfa'), {'arama': '8691112223334'})
        alt_kategori_response = self.client.get(
            reverse('ana_sayfa'), {'ana_kategori': self.kategori.parent_id, 'alt_kategori': self.kategori.id},
        )

        self.assertContains(ana_kategori_response, 'PVC Dirsek')
        self.assertNotContains(ana_kategori_response, 'Seramik Klozet')
        self.assertContains(barkod_response, 'PVC Dirsek')
        self.assertContains(alt_kategori_response, 'PVC Dirsek')

    def test_urun_listesi_canli_filtreleme_bilesenlerini_sunar(self):
        response = self.client.get(reverse('ana_sayfa'))

        self.assertContains(response, 'urunFiltreFormu')
        self.assertContains(response, 'canliFiltrele')
        self.assertContains(response, 'Sonuçlar otomatik yenilenir')

    def test_urun_duzenleme_bilgileri_ve_barkodu_gunceller(self):
        urun = Urun.objects.create(
            ad='Eski Ürün', kategori=self.kategori, alis_fiyati='10.00', satis_fiyati='15.00', stok_miktari=2,
        )
        Barkod.objects.create(urun=urun, barkod_no='8690000000001')

        response = self.client.post(
            reverse('urun_duzenle', args=[urun.id]),
            {
                'ad': 'Güncel Ürün', 'kategori': self.kategori.id, 'alis_fiyati': '12', 'satis_fiyati': '20',
                'stok_miktari': 7, 'kritik_stok_seviyesi': 3, 'barkod_no': '8690000000002',
            },
        )

        self.assertRedirects(response, reverse('urun_detay', args=[urun.id]))
        urun.refresh_from_db()
        self.assertEqual(urun.ad, 'Güncel Ürün')
        self.assertEqual(urun.stok_miktari, 7)
        self.assertTrue(Barkod.objects.filter(urun=urun, barkod_no='8690000000002').exists())

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
