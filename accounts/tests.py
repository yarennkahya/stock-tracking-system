from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from datetime import date, timedelta

from .models import Firma, Senet


class HesapAkisiTestleri(TestCase):
    def test_giris_ekrani_uygulama_menusu_yerine_karsilama_duzenini_kullanir(self):
        response = self.client.get(reverse('login'))

        self.assertContains(response, 'auth-shell')
        self.assertContains(response, 'İşletmenizin günlük akışı tek ekranda.')
        self.assertNotContains(response, 'class="sidebar d-flex flex-column"')
        self.assertNotContains(response, 'id="mobileSidebar"')

    def test_yaklasan_senet_yedi_gunluk_listede_gorunur(self):
        user = User.objects.create_user('deneme_kullanici', 'deneme@example.com', 'GucluSifre123!')
        firma = Firma.objects.create(ad='Demo Firma')
        senet = Senet.objects.create(
            firma=firma, tip='alacak', tutar='5000.00', vade_tarihi=date.today() + timedelta(days=3),
        )
        self.client.force_login(user)

        response = self.client.get(reverse('senet_takip'))

        self.assertContains(response, 'Yaklaşan Vadeler')
        self.assertContains(response, firma.ad)
        self.assertContains(response, '5000,00')

    def test_firma_ekleme_ekranindan_firma_kaydedilir(self):
        user = User.objects.create_user('deneme_kullanici', 'deneme@example.com', 'GucluSifre123!')
        self.client.force_login(user)

        response = self.client.post(
            reverse('firma_ekle'),
            {'ad': 'Yeni Tedarikçi', 'telefon': '05320000000', 'adres': 'İstanbul'},
        )

        self.assertRedirects(response, reverse('firma_listesi'))
        self.assertTrue(Firma.objects.filter(ad='Yeni Tedarikçi').exists())

    def test_firma_duzenlenip_pasife_alinabilir(self):
        user = User.objects.create_user('deneme_kullanici', 'deneme@example.com', 'GucluSifre123!')
        firma = Firma.objects.create(ad='Eski Firma', telefon='02120000000')
        self.client.force_login(user)

        response = self.client.post(
            reverse('firma_duzenle', args=[firma.id]),
            {'ad': 'Güncel Firma', 'telefon': '05320000000', 'adres': 'İstanbul'},
        )

        self.assertRedirects(response, reverse('firma_listesi'))
        firma.refresh_from_db()
        self.assertEqual(firma.ad, 'Güncel Firma')
        self.assertEqual(firma.telefon, '05320000000')

        response = self.client.post(reverse('firma_durum_degistir', args=[firma.id]), {'gorunum': 'aktif'})

        self.assertRedirects(response, f'{reverse("firma_listesi")}?gorunum=aktif')
        firma.refresh_from_db()
        self.assertFalse(firma.aktif)
        self.assertContains(self.client.get(f'{reverse("firma_listesi")}?gorunum=pasif'), 'Güncel Firma')

    def test_senet_ekleme_ekranindan_senet_kaydedilir(self):
        user = User.objects.create_user('deneme_kullanici', 'deneme@example.com', 'GucluSifre123!')
        firma = Firma.objects.create(ad='Yeni Tedarikçi')
        self.client.force_login(user)

        response = self.client.post(
            reverse('senet_ekle'),
            {
                'firma': firma.id, 'tip': 'borc', 'tutar': '1250.50',
                'vade_tarihi': date.today() + timedelta(days=5), 'durum': 'bekliyor', 'aciklama': 'Mal alım senedi',
            },
        )

        self.assertRedirects(response, reverse('senet_takip'))
        self.assertTrue(Senet.objects.filter(firma=firma, tutar='1250.50').exists())

    def test_senet_duzenlenip_pasife_alinabilir_ve_silinebilir(self):
        user = User.objects.create_user('deneme_kullanici', 'deneme@example.com', 'GucluSifre123!')
        firma = Firma.objects.create(ad='Yeni Tedarikçi')
        senet = Senet.objects.create(
            firma=firma, tip='borc', tutar='1250.50', vade_tarihi=date.today() + timedelta(days=5),
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('senet_duzenle', args=[senet.id]),
            {
                'firma': firma.id, 'tip': 'alacak', 'tutar': '1600.00',
                'vade_tarihi': date.today() + timedelta(days=8), 'durum': 'bekliyor', 'aciklama': 'Güncellendi',
            },
        )

        self.assertRedirects(response, reverse('senet_takip'))
        senet.refresh_from_db()
        self.assertEqual(senet.tip, 'alacak')
        self.assertEqual(str(senet.tutar), '1600.00')

        response = self.client.post(reverse('senet_durum_degistir', args=[senet.id]), {'gorunum': 'aktif'})
        self.assertRedirects(response, f'{reverse("senet_takip")}?gorunum=aktif')
        senet.refresh_from_db()
        self.assertFalse(senet.aktif)
        pasif_liste = self.client.get(f'{reverse("senet_takip")}?gorunum=pasif')
        self.assertContains(pasif_liste, '1600,00')
        self.assertTrue(pasif_liste.context['pasif_senetler'].filter(id=senet.id).exists())

        response = self.client.post(reverse('senet_sil', args=[senet.id]), {'gorunum': 'pasif'})
        self.assertRedirects(response, f'{reverse("senet_takip")}?gorunum=pasif')
        self.assertFalse(Senet.objects.filter(id=senet.id).exists())

    def test_giris_yapan_kullanici_hesap_ozetini_gorur(self):
        user = User.objects.create_user(
            'deneme_kullanici',
            'deneme@example.com',
            'GucluSifre123!',
            first_name='Ada',
            last_name='Yılmaz',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('ana_sayfa'))

        self.assertContains(response, 'Ada Yılmaz')
        self.assertContains(response, '@deneme_kullanici')
        self.assertContains(response, reverse('hesap_ayarlari'))
        self.assertContains(response, 'class="theme-toggle" data-theme-toggle', count=2)
        self.assertNotContains(response, 'themeToggleBtn')
        self.assertNotContains(response, 'href="/admin/"')

    def test_hesap_ayarlari_bilgileri_gunceller(self):
        user = User.objects.create_user('eski_kullanici', 'eski@example.com', 'GucluSifre123!')
        self.client.force_login(user)

        response = self.client.post(
            reverse('hesap_ayarlari'),
            {
                'username': 'yeni_kullanici',
                'first_name': 'Ada',
                'last_name': 'Yılmaz',
                'email': 'yeni@example.com',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.username, 'yeni_kullanici')
        self.assertEqual(user.get_full_name(), 'Ada Yılmaz')
        self.assertEqual(user.email, 'yeni@example.com')
        self.assertContains(response, 'Hesap bilgileriniz güncellendi.')

    def test_hesap_ayarlari_baskasinin_epostasini_kabul_etmez(self):
        user = User.objects.create_user('deneme_kullanici', 'deneme@example.com', 'GucluSifre123!')
        User.objects.create_user('diger_kullanici', 'diger@example.com', 'GucluSifre123!')
        self.client.force_login(user)

        response = self.client.post(
            reverse('hesap_ayarlari'),
            {
                'username': 'deneme_kullanici',
                'first_name': '',
                'last_name': '',
                'email': 'diger@example.com',
            },
        )

        self.assertFormError(
            response.context['form'],
            'email',
            'Bu e-posta adresi başka bir hesap tarafından kullanılıyor.',
        )

    def test_hesap_ayarlari_giris_gerektirir(self):
        response = self.client.get(reverse('hesap_ayarlari'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('hesap_ayarlari')}")

    def test_dil_secimi_ingilizceye_gecer_ve_sayfada_kalir(self):
        user = User.objects.create_user('deneme_kullanici', 'deneme@example.com', 'GucluSifre123!')
        self.client.force_login(user)

        turkce_sayfa = self.client.get(reverse('ana_sayfa'))
        self.assertContains(turkce_sayfa, '>EN</button>', count=2)
        self.assertNotContains(turkce_sayfa, '>TR</button>')

        response = self.client.post(
            reverse('set_language'),
            {'language': 'en', 'next': reverse('ana_sayfa')},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'], reverse('ana_sayfa'))
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, 'en')
        self.assertContains(response, 'Products')
        self.assertContains(response, '>TR</button>', count=2)
        self.assertNotContains(response, '>EN</button>')

    def test_uye_ol_kullanici_olusturur_ve_giris_yapar(self):
        response = self.client.post(
            reverse('uye_ol'),
            {
                'username': 'deneme_kullanici',
                'email': 'deneme@example.com',
                'password1': 'GucluSifre123!',
                'password2': 'GucluSifre123!',
            },
        )

        self.assertRedirects(response, reverse('ana_sayfa'))
        self.assertTrue(User.objects.filter(username='deneme_kullanici').exists())
        self.assertEqual(self.client.session.get('_auth_user_id'), str(User.objects.get(username='deneme_kullanici').pk))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_sifre_sifirlama_baglantisi_gonderir(self):
        User.objects.create_user('deneme_kullanici', 'deneme@example.com', 'GucluSifre123!')

        response = self.client.post(reverse('password_reset'), {'email': 'deneme@example.com'})

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/sifre-yenile/', mail.outbox[0].body)
