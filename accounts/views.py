from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .models import Firma, Senet


@login_required
def firma_listesi(request):
    firmalar = Firma.objects.all()
    return render(request, 'firma_listesi.html', {'firmalar': firmalar})


@login_required
def senet_takip(request):
    bugun = date.today()
    yaklasan_tarih = bugun + timedelta(days=7)

    gecikmis = Senet.objects.filter(durum='bekliyor', vade_tarihi__lt=bugun)
    yaklasan = Senet.objects.filter(durum='bekliyor', vade_tarihi__gte=bugun, vade_tarihi__lte=yaklasan_tarih)
    diger_bekleyenler = Senet.objects.filter(durum='bekliyor', vade_tarihi__gt=yaklasan_tarih)

    return render(request, 'senet_takip.html', {
        'gecikmis': gecikmis,
        'yaklasan': yaklasan,
        'diger_bekleyenler': diger_bekleyenler,
    })