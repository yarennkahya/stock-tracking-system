from django.db import models


class Firma(models.Model):
    ad = models.CharField(max_length=200)
    telefon = models.CharField(max_length=20, blank=True, null=True)
    adres = models.TextField(blank=True, null=True)

    def bakiye(self):
        borclar = self.senetler.filter(tip='borc', durum__in=['bekliyor', 'gecikti']).aggregate(
            toplam=models.Sum('tutar'))['toplam'] or 0
        alacaklar = self.senetler.filter(tip='alacak', durum__in=['bekliyor', 'gecikti']).aggregate(
            toplam=models.Sum('tutar'))['toplam'] or 0
        return alacaklar - borclar

    def __str__(self):
        return self.ad


class Senet(models.Model):
    TIP_SECENEKLERI = [
        ('borc', 'Borç (Bizim Ödeyeceğimiz)'),
        ('alacak', 'Alacak (Bize Ödenecek)'),
    ]
    DURUM_SECENEKLERI = [
        ('bekliyor', 'Bekliyor'),
        ('odendi', 'Ödendi'),
        ('gecikti', 'Gecikti'),
    ]

    firma = models.ForeignKey(Firma, on_delete=models.CASCADE, related_name='senetler')
    tip = models.CharField(max_length=10, choices=TIP_SECENEKLERI)
    tutar = models.DecimalField(max_digits=10, decimal_places=2)
    vade_tarihi = models.DateField()
    durum = models.CharField(max_length=10, choices=DURUM_SECENEKLERI, default='bekliyor')
    aciklama = models.CharField(max_length=255, blank=True, null=True)
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.firma.ad} - {self.tutar} ₺ - {self.get_durum_display()}"