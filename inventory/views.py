from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from .forms import KategoriFormu, UrunForm
from .models import Barkod, Kategori, StokHareketi, Urun


@login_required
def ana_sayfa(request):
    urunler = Urun.objects.select_related('kategori').all()
    return render(request, 'ana_sayfa.html', {'urunler': urunler})


@login_required
def urun_detay(request, urun_id):
    urun = get_object_or_404(Urun.objects.select_related('kategori'), id=urun_id)
    return render(request, 'urun_detay.html', {'urun': urun})


@login_required
def barkod_sorgula(request, barkod_no):
    barkod = Barkod.objects.select_related('urun__kategori').filter(barkod_no=barkod_no).first()
    if not barkod:
        return JsonResponse({'bulundu': False}, status=404)
    urun = barkod.urun
    return JsonResponse({
        'bulundu': True, 'urun_id': urun.id, 'ad': urun.ad, 'kategori': str(urun.kategori),
        'satis_fiyati': str(urun.satis_fiyati), 'stok_miktari': urun.stok_miktari,
    })


@login_required
def barkod_tara(request):
    return render(request, 'barkod_tara.html')


@login_required
def urun_ekle(request):
    onceki_barkod = request.GET.get('barkod', '')
    form = UrunForm(request.POST or None, initial={'barkod_no': onceki_barkod})
    if request.method == 'POST' and form.is_valid():
        urun = form.save()
        barkod_no = form.cleaned_data.get('barkod_no')
        if barkod_no:
            Barkod.objects.create(urun=urun, barkod_no=barkod_no)
        return redirect('urun_detay', urun_id=urun.id)
    return render(request, 'urun_ekle.html', {'form': form})


@login_required
def kategori_listesi(request):
    form = KategoriFormu(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Kategori kaydedildi.')
        return redirect('kategori_listesi')
    ana_kategoriler = Kategori.objects.filter(parent__isnull=True).prefetch_related('alt_kategoriler')
    return render(request, 'kategori_listesi.html', {'form': form, 'ana_kategoriler': ana_kategoriler})


@login_required
@require_GET
def alt_kategoriler(request, ana_kategori_id):
    altlar = Kategori.objects.filter(parent_id=ana_kategori_id).order_by('ad')
    return JsonResponse({'alt_kategoriler': [{'id': kategori.id, 'ad': kategori.ad} for kategori in altlar]})


@login_required
def hizli_urun_ekle(request):
    ana_kategoriler = Kategori.objects.filter(parent__isnull=True).order_by('ad')
    return render(request, 'hizli_urun_ekle.html', {'ana_kategoriler': ana_kategoriler})


@login_required
def barkod_kontrol(request, barkod_no):
    barkod = Barkod.objects.select_related('urun').filter(barkod_no=barkod_no).first()
    if not barkod:
        return JsonResponse({'bulundu': False})
    return JsonResponse({
        'bulundu': True, 'urun_id': barkod.urun.id, 'ad': barkod.urun.ad,
        'stok_miktari': barkod.urun.stok_miktari,
    })


@login_required
def hizli_stok_ekle(request, urun_id):
    if request.method != 'POST':
        return JsonResponse({'basarili': False}, status=405)
    urun = get_object_or_404(Urun, id=urun_id)
    urun.stok_miktari += 1
    urun.save(update_fields=['stok_miktari'])
    StokHareketi.objects.create(urun=urun, hareket_tipi='giris', miktar=1, aciklama='Hızlı ekleme ekranı')
    return JsonResponse({'basarili': True, 'yeni_stok': urun.stok_miktari})


@login_required
def hizli_urun_kaydet(request):
    if request.method != 'POST':
        return JsonResponse({'basarili': False}, status=405)

    barkod_no = request.POST.get('barkod_no', '').strip()
    ad = request.POST.get('ad', '').strip()
    kategori_id = request.POST.get('kategori_id')
    alis_fiyati = request.POST.get('alis_fiyati') or 0
    satis_fiyati = request.POST.get('satis_fiyati') or 0
    stok_miktari = request.POST.get('stok_miktari') or 1

    if not ad or not kategori_id:
        return JsonResponse({'basarili': False, 'hata': 'Ürün adı ve alt kategori zorunlu.'}, status=400)
    if barkod_no and Barkod.objects.filter(barkod_no=barkod_no).exists():
        return JsonResponse({'basarili': False, 'hata': 'Bu barkod zaten kayıtlı.'}, status=400)

    kategori = get_object_or_404(Kategori, id=kategori_id, parent__isnull=False)
    try:
        stok_miktari = int(stok_miktari)
    except (TypeError, ValueError):
        return JsonResponse({'basarili': False, 'hata': 'Stok miktarı geçerli bir sayı olmalıdır.'}, status=400)
    if stok_miktari < 0:
        return JsonResponse({'basarili': False, 'hata': 'Stok miktarı negatif olamaz.'}, status=400)

    with transaction.atomic():
        urun = Urun.objects.create(
            ad=ad, kategori=kategori, alis_fiyati=alis_fiyati,
            satis_fiyati=satis_fiyati, stok_miktari=stok_miktari,
        )
        if barkod_no:
            Barkod.objects.create(urun=urun, barkod_no=barkod_no)
        if stok_miktari > 0:
            StokHareketi.objects.create(
                urun=urun, hareket_tipi='giris', miktar=stok_miktari, aciklama='Hızlı ekleme ekranı',
            )

    return JsonResponse({'basarili': True, 'urun_id': urun.id, 'ad': urun.ad, 'kategori_id': kategori.id})
