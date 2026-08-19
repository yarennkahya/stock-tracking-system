from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from datetime import date, timedelta
from .forms import FirmaFormu, HesapAyarlariFormu, SenetFormu, UyeOlFormu
from .models import Firma, Senet


def uye_ol(request):
    if request.user.is_authenticated:
        return redirect('ana_sayfa')

    if request.method == 'POST':
        form = UyeOlFormu(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Hesabınız oluşturuldu. Hoş geldiniz!')
            return redirect('ana_sayfa')
    else:
        form = UyeOlFormu()

    return render(request, 'uye_ol.html', {'form': form})


@login_required
def hesap_ayarlari(request):
    if request.method == 'POST':
        form = HesapAyarlariFormu(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Hesap bilgileriniz güncellendi.'))
            return redirect('hesap_ayarlari')
    else:
        form = HesapAyarlariFormu(instance=request.user)

    return render(request, 'hesap_ayarlari.html', {'form': form})


@login_required
def firma_listesi(request):
    firmalar = Firma.objects.order_by('ad')
    return render(request, 'firma_listesi.html', {'firmalar': firmalar})


@login_required
def firma_ekle(request):
    form = FirmaFormu(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        firma = form.save()
        messages.success(request, f'{firma.ad} firması eklendi.')
        return redirect('firma_listesi')
    return render(request, 'firma_formu.html', {'form': form})


@login_required
def senet_takip(request):
    bugun = date.today()
    yaklasan_tarih = bugun + timedelta(days=7)

    gecikmis = Senet.objects.select_related('firma').filter(durum='bekliyor', vade_tarihi__lt=bugun)
    yaklasan = Senet.objects.select_related('firma').filter(durum='bekliyor', vade_tarihi__gte=bugun, vade_tarihi__lte=yaklasan_tarih)
    diger_bekleyenler = Senet.objects.select_related('firma').filter(durum='bekliyor', vade_tarihi__gt=yaklasan_tarih)

    return render(request, 'senet_takip.html', {
        'gecikmis': gecikmis,
        'yaklasan': yaklasan,
        'diger_bekleyenler': diger_bekleyenler,
    })


@login_required
def senet_ekle(request):
    form = SenetFormu(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        senet = form.save()
        messages.success(request, f'{senet.firma.ad} için senet eklendi.')
        return redirect('senet_takip')
    return render(request, 'senet_formu.html', {'form': form, 'firma_var_mi': Firma.objects.exists()})
