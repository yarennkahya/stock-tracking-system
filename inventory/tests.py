from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Barkod, Kategori, Urun


class HizliUrunEklemeTestleri(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('depo', 'depo@example.com', 'GucluSifre123!')
        self.client.force_login(self.user)
        self.kategori = Kategori.objects.create(ad='Boru ve ek parçaları')

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
