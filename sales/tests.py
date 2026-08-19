from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from inventory.models import Barkod, Kategori, StokHareketi, Urun
from .models import Satis


class SatisAkisiTestleri(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('satici', 'satici@example.com', 'GucluSifre123!')
        self.client.force_login(self.user)
        kategori = Kategori.objects.create(ad='Vitrifiye')
        self.urun = Urun.objects.create(
            ad='Seramik Klozet', kategori=kategori, alis_fiyati='900.00',
            satis_fiyati='1250.00', stok_miktari=2,
        )
        Barkod.objects.create(urun=self.urun, barkod_no='8691234567890')

    def test_urun_adi_yazdikca_aranabilir(self):
        sayfa = self.client.get(reverse('satis_ekrani'))
        response = self.client.get(reverse('urun_ara'), {'q': 'klo'})

        self.assertContains(sayfa, 'urunAramaInput')
        self.assertContains(sayfa, 'sepet-verisi')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['sonuclar'][0]['ad'], 'Seramik Klozet')
        self.assertEqual(response.json()['sonuclar'][0]['satis_fiyati'], '1250.00')

    def test_barkod_okutulan_urun_sepete_eklenir(self):
        response = self.client.post(reverse('sepete_barkod_ekle'), {'barkod_no': '8691234567890'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['basarili'])
        self.assertEqual(response.json()['sepet']['kalemler'][0]['miktar'], 1)
        self.assertEqual(self.client.session['sepet'][str(self.urun.id)]['miktar'], 1)

    def test_sepet_stoktan_fazla_artirilamaz(self):
        self.client.post(reverse('sepete_urun_ekle', args=[self.urun.id]))
        ikinci_ekleme = self.client.post(reverse('sepete_urun_ekle', args=[self.urun.id]))
        stok_asan_ekleme = self.client.post(reverse('sepete_urun_ekle', args=[self.urun.id]))

        self.assertEqual(ikinci_ekleme.json()['sepet']['kalemler'][0]['miktar'], 2)
        self.assertEqual(stok_asan_ekleme.status_code, 400)
        self.assertIn('Yetersiz stok', stok_asan_ekleme.json()['hata'])

    def test_satis_tamamlaninca_stok_ve_hareket_guncellenir(self):
        self.client.post(reverse('sepete_urun_ekle', args=[self.urun.id]))

        response = self.client.post(reverse('satisi_tamamla'))

        satis = Satis.objects.get()
        self.assertRedirects(response, reverse('satis_detay', args=[satis.id]))
        self.urun.refresh_from_db()
        self.assertEqual(self.urun.stok_miktari, 1)
        self.assertEqual(satis.toplam_tutar, Decimal('1250.00'))
        self.assertEqual(satis.odeme_yontemi, 'nakit')
        self.assertEqual(satis.pos_islem_no, '')
        self.assertTrue(StokHareketi.objects.filter(urun=self.urun, hareket_tipi='cikis', miktar=1).exists())

    def test_kart_satisi_demo_pos_onayi_ile_tamamlanir(self):
        self.client.post(reverse('sepete_urun_ekle', args=[self.urun.id]))

        response = self.client.post(
            reverse('satisi_tamamla'),
            {'odeme_yontemi': 'kart', 'pos_onay': '1', 'pos_islem_no': 'DEMO-POS-123456789-1234'},
        )

        satis = Satis.objects.get()
        self.assertRedirects(response, reverse('satis_detay', args=[satis.id]))
        self.assertEqual(satis.odeme_yontemi, 'kart')
        self.assertEqual(satis.pos_islem_no, 'DEMO-POS-123456789-1234')
        self.urun.refresh_from_db()
        self.assertEqual(self.urun.stok_miktari, 1)

    def test_kart_satisi_demo_pos_onayi_olmadan_tamamlanmaz(self):
        self.client.post(reverse('sepete_urun_ekle', args=[self.urun.id]))

        response = self.client.post(reverse('satisi_tamamla'), {'odeme_yontemi': 'kart'})

        self.assertRedirects(response, reverse('satis_ekrani'))
        self.assertEqual(Satis.objects.count(), 0)
        self.urun.refresh_from_db()
        self.assertEqual(self.urun.stok_miktari, 2)
        self.assertIn(str(self.urun.id), self.client.session['sepet'])
