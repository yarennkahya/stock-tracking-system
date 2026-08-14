from django.db import models
from django.contrib.auth.models import User
from inventory.models import Urun


class Satis(models.Model):
    satisi_yapan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    toplam_tutar = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Satış #{self.id} - {self.tarih.strftime('%d.%m.%Y %H:%M')}"


class SatisKalemi(models.Model):
    satis = models.ForeignKey(Satis, on_delete=models.CASCADE, related_name='kalemler')
    urun = models.ForeignKey(Urun, on_delete=models.PROTECT)
    miktar = models.PositiveIntegerField()
    birim_fiyat = models.DecimalField(max_digits=10, decimal_places=2)

    def toplam(self):
        return self.miktar * self.birim_fiyat

    def __str__(self):
        return f"{self.urun.ad} x {self.miktar}"