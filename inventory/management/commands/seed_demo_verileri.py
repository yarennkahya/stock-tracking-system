from datetime import date, timedelta

from django.core.management.base import BaseCommand

from accounts.models import Firma, Senet
from inventory.models import Barkod, Kategori, Urun


KATEGORI_AGACI = {
    'Boru ve Ek Parçaları': ['PVC Boru ve Ek Parçaları', 'PPRC Boru ve Ek Parçaları', 'Atık Su ve Sifonlar'],
    'Vana ve Armatür': ['Küresel Vana', 'Ara Musluk ve Stop Vana', 'Batarya ve Musluklar'],
    'Vitrifiye': ['Klozetler', 'Lavabolar', 'Rezervuar ve İç Takım'],
    'Isıtma': ['Kombi Bağlantı Malzemeleri', 'Radyatör Vanaları', 'Kollektör ve PEX'],
    'Bağlantı ve Montaj': ['Rakor ve Nipeller', 'Conta ve Kelepçe', 'Teflon ve Sızdırmazlık'],
    'El Aletleri': ['Kesme ve Sıkma Aletleri', 'Ölçüm Aletleri'],
}

URUNLER = [
    ('Boru ve Ek Parçaları', 'PVC Boru ve Ek Parçaları', 'PVC Dirsek 50 mm', '12', '20', 30, '8690000000001'),
    ('Boru ve Ek Parçaları', 'PPRC Boru ve Ek Parçaları', 'PPRC Boru 25 mm - 4 m', '95', '135', 18, '8690000000002'),
    ('Vana ve Armatür', 'Küresel Vana', '1/2 Pirinç Küresel Vana', '110', '165', 15, '8690000000003'),
    ('Vana ve Armatür', 'Batarya ve Musluklar', 'Lavabo Bataryası', '780', '1150', 8, '8690000000004'),
    ('Vitrifiye', 'Klozetler', 'Seramik Klozet Takımı', '3100', '4450', 4, '8690000000005'),
    ('Vitrifiye', 'Rezervuar ve İç Takım', 'Gömme Rezervuar İç Takım', '420', '610', 10, '8690000000006'),
    ('Bağlantı ve Montaj', 'Teflon ve Sızdırmazlık', 'Teflon Bant', '8', '15', 50, '8690000000007'),
    ('Bağlantı ve Montaj', 'Conta ve Kelepçe', '50 mm Boru Kelepçesi', '18', '30', 40, '8690000000008'),
]


class Command(BaseCommand):
    help = 'Tesisatçı dükkânı için kategori, ürün, firma ve yaklaşan vadeli senet örneklerini ekler.'

    def handle(self, *args, **options):
        kategoriler = {}
        for ana_ad, alt_adlar in KATEGORI_AGACI.items():
            ana_kategori, _ = Kategori.objects.get_or_create(ad=ana_ad, parent=None)
            for alt_ad in alt_adlar:
                kategoriler[(ana_ad, alt_ad)], _ = Kategori.objects.get_or_create(ad=alt_ad, parent=ana_kategori)

        for ana_ad, alt_ad, urun_ad, alis, satis, stok, barkod_no in URUNLER:
            urun, _ = Urun.objects.update_or_create(
                ad=urun_ad,
                kategori=kategoriler[(ana_ad, alt_ad)],
                defaults={'alis_fiyati': alis, 'satis_fiyati': satis, 'stok_miktari': stok},
            )
            Barkod.objects.update_or_create(barkod_no=barkod_no, defaults={'urun': urun})

        firma, _ = Firma.objects.get_or_create(
            ad='Demo Tesisat Tedarik',
            defaults={'telefon': '0212 555 10 10', 'adres': 'İstanbul'},
        )
        bugun = date.today()
        Senet.objects.get_or_create(
            firma=firma, tip='alacak', vade_tarihi=bugun + timedelta(days=3),
            defaults={'tutar': '12500.00', 'durum': 'bekliyor', 'aciklama': 'Demo yaklaşan alacak senedi'},
        )
        Senet.objects.get_or_create(
            firma=firma, tip='borc', vade_tarihi=bugun + timedelta(days=6),
            defaults={'tutar': '6850.00', 'durum': 'bekliyor', 'aciklama': 'Demo yaklaşan borç senedi'},
        )
        self.stdout.write(self.style.SUCCESS('Demo kategori, ürün, firma ve senet verileri hazır.'))
