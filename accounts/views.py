from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.urls import reverse
from django.views.decorators.http import require_POST
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
    gorunum = request.GET.get('gorunum', 'aktif')
    if gorunum == 'pasif':
        firmalar = Firma.objects.filter(aktif=False)
    elif gorunum == 'tum':
        firmalar = Firma.objects.all()
    else:
        gorunum = 'aktif'
        firmalar = Firma.objects.filter(aktif=True)
    return render(request, 'firma_listesi.html', {'firmalar': firmalar.order_by('ad'), 'gorunum': gorunum})


@login_required
def firma_ekle(request):
    form = FirmaFormu(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        firma = form.save()
        messages.success(request, f'{firma.ad} firması eklendi.')
        return redirect('firma_listesi')
    return render(request, 'firma_formu.html', {
        'form': form,
        'sayfa_basligi': 'Firma Ekle',
        'sayfa_aciklamasi': 'Tedarikçi veya müşteri firmanın iletişim bilgilerini kaydedin.',
        'submit_etiketi': 'Firmayı Kaydet',
    })


@login_required
def firma_duzenle(request, firma_id):
    firma = get_object_or_404(Firma, id=firma_id)
    form = FirmaFormu(request.POST or None, instance=firma)
    if request.method == 'POST' and form.is_valid():
        firma = form.save()
        messages.success(request, f'{firma.ad} firması güncellendi.')
        return redirect('firma_listesi')
    return render(request, 'firma_formu.html', {
        'form': form,
        'firma': firma,
        'sayfa_basligi': 'Firma Düzenle',
        'sayfa_aciklamasi': f'{firma.ad} firmasının iletişim bilgilerini güncelleyin.',
        'submit_etiketi': 'Değişiklikleri Kaydet',
    })


@login_required
@require_POST
def firma_durum_degistir(request, firma_id):
    firma = get_object_or_404(Firma, id=firma_id)
    firma.aktif = not firma.aktif
    firma.save(update_fields=['aktif'])
    mesaj = 'Firmayı tekrar aktif yaptınız.' if firma.aktif else 'Firma pasife alındı.'
    messages.success(request, mesaj)
    gorunum = request.POST.get('gorunum', 'aktif')
    if gorunum not in {'aktif', 'pasif', 'tum'}:
        gorunum = 'aktif'
    return redirect(f'{reverse("firma_listesi")}?gorunum={gorunum}')


@login_required
def senet_takip(request):
    bugun = date.today()
    yaklasan_tarih = bugun + timedelta(days=7)
    gorunum = request.GET.get('gorunum', 'aktif')

    if gorunum == 'pasif':
        pasif_senetler = Senet.objects.select_related('firma').filter(aktif=False).order_by('-vade_tarihi')
        return render(request, 'senet_takip.html', {
            'gorunum': 'pasif',
            'pasif_senetler': pasif_senetler,
        })

    gecikmis = Senet.objects.select_related('firma').filter(aktif=True, durum='bekliyor', vade_tarihi__lt=bugun)
    yaklasan = Senet.objects.select_related('firma').filter(aktif=True, durum='bekliyor', vade_tarihi__gte=bugun, vade_tarihi__lte=yaklasan_tarih)
    diger_bekleyenler = Senet.objects.select_related('firma').filter(aktif=True, durum='bekliyor', vade_tarihi__gt=yaklasan_tarih)

    return render(request, 'senet_takip.html', {
        'gorunum': 'aktif',
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
    return render(request, 'senet_formu.html', {
        'form': form,
        'firma_var_mi': Firma.objects.filter(aktif=True).exists(),
        'sayfa_basligi': 'Senet Ekle',
        'sayfa_aciklamasi': 'Firma, vade ve tutar bilgisini girerek senedi takibe alın.',
        'submit_etiketi': 'Senedi Kaydet',
    })


@login_required
def senet_duzenle(request, senet_id):
    senet = get_object_or_404(Senet, id=senet_id)
    form = SenetFormu(request.POST or None, instance=senet)
    if request.method == 'POST' and form.is_valid():
        senet = form.save()
        messages.success(request, f'{senet.firma.ad} için senet güncellendi.')
        return redirect('senet_takip')
    return render(request, 'senet_formu.html', {
        'form': form,
        'senet': senet,
        'firma_var_mi': True,
        'sayfa_basligi': 'Senet Düzenle',
        'sayfa_aciklamasi': f'{senet.firma.ad} firmasına ait senet bilgilerini güncelleyin.',
        'submit_etiketi': 'Değişiklikleri Kaydet',
    })


@login_required
@require_POST
def senet_durum_degistir(request, senet_id):
    senet = get_object_or_404(Senet, id=senet_id)
    senet.aktif = not senet.aktif
    senet.save(update_fields=['aktif'])
    mesaj = 'Senet tekrar aktif takibe alındı.' if senet.aktif else 'Senet pasife alındı.'
    messages.success(request, mesaj)
    gorunum = request.POST.get('gorunum', 'aktif')
    return redirect(f'{reverse("senet_takip")}?gorunum={"pasif" if gorunum == "pasif" else "aktif"}')


@login_required
@require_POST
def senet_sil(request, senet_id):
    senet = get_object_or_404(Senet, id=senet_id)
    firma_adi = senet.firma.ad
    senet.delete()
    messages.success(request, f'{firma_adi} firmasına ait senet silindi.')
    gorunum = request.POST.get('gorunum', 'aktif')
    return redirect(f'{reverse("senet_takip")}?gorunum={"pasif" if gorunum == "pasif" else "aktif"}')
