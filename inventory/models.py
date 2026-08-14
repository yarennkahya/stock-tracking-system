from django.db import models

class Kategori(models.Model):
    ad = models.CharField(max_length=100)
    aciklama = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.ad


class Urun(models.Model):
    ad = models.CharField(max_length=200)
    kategori = models.ForeignKey(Kategori, on_delete=models.CASCADE, related_name='urunler')
    alis_fiyati = models.DecimalField(max_digits=10, decimal_places=2)
    satis_fiyati = models.DecimalField(max_digits=10, decimal_places=2)
    stok_miktari = models.PositiveIntegerField(default=0)
    kritik_stok_seviyesi = models.PositiveIntegerField(default=5)
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ad


class Barkod(models.Model):
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, related_name='barkodlar')
    barkod_no = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.barkod_no


class StokHareketi(models.Model):
    HAREKET_TIPLERI = [
        ('giris', 'Stok Girişi'),
        ('cikis', 'Stok Çıkışı'),
    ]

    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, related_name='hareketler')
    hareket_tipi = models.CharField(max_length=10, choices=HAREKET_TIPLERI)
    miktar = models.PositiveIntegerField()
    aciklama = models.CharField(max_length=255, blank=True, null=True)
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.urun.ad} - {self.get_hareket_tipi_display()} - {self.miktar}"
