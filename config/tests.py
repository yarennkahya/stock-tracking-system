from django.test import SimpleTestCase
from django.urls import reverse


class ModulerUrlYapisiTestleri(SimpleTestCase):
    def test_uygulama_url_isimleri_mevcut_adresleri_korur(self):
        self.assertEqual(reverse('login'), '/giris/')
        self.assertEqual(reverse('ana_sayfa'), '/')
        self.assertEqual(reverse('urun_ekle'), '/urun/ekle/')
        self.assertEqual(reverse('satis_ekrani'), '/satis/')
        self.assertEqual(reverse('firma_listesi'), '/firmalar/')
        self.assertEqual(reverse('senet_takip'), '/senet-takip/')
