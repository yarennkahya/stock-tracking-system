from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Urun, Barkod
from .forms import UrunForm
from .models import Barkod
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from .models import Urun, Barkod, Kategori, StokHareketi
from .forms import UrunForm

@login_required
def ana_sayfa(request):
    urunler = Urun.objects.all()
    return render(request, 'ana_sayfa.html', {'urunler': urunler})


@login_required
def urun_detay(request, urun_id):
    urun = get_object_or_404(Urun, id=urun_id)
    return render(request, 'urun_detay.html', {'urun': urun})


@login_required
def barkod_sorgula(request, barkod_no):
    try:
        barkod = Barkod.objects.get(barkod_no=barkod_no)
        urun = barkod.urun
        return JsonResponse({
            'bulundu': True,
            'urun_id': urun.id,
            'ad': urun.ad,
            'kategori': str(urun.kategori),
            'satis_fiyati': str(urun.satis_fiyati),
            'stok_miktari': urun.stok_miktari,
        })
    except Barkod.DoesNotExist:
        return JsonResponse({'bulundu': False}, status=404)


@login_required
def barkod_tara(request):
    return render(request, 'barkod_tara.html')

@login_required
def urun_ekle(request):
    onceki_barkod = request.GET.get('barkod', '')
    if request.method == 'POST':
        form = UrunForm(request.POST)
        if form.is_valid():
            urun = form.save()
            barkod_no = form.cleaned_data.get('barkod_no')
            if barkod_no:
                Barkod.objects.create(urun=urun, barkod_no=barkod_no)
            return redirect('urun_detay', urun_id=urun.id)
    else:
        form = UrunForm(initial={'barkod_no': onceki_barkod})
    return render(request, 'urun_ekle.html', {'form': form})

@login_required
def hizli_urun_ekle(request):
    kategoriler = Kategori.objects.all()
    return render(request, 'hizli_urun_ekle.html', {'kategoriler': kategoriler})


@login_required
def barkod_kontrol(request, barkod_no):
    try:
        barkod = Barkod.objects.get(barkod_no=barkod_no)
        urun = barkod.urun
        return JsonResponse({
            'bulundu': True,
            'urun_id': urun.id,
            'ad': urun.ad,
            'stok_miktari': urun.stok_miktari,
        })
    except Barkod.DoesNotExist:
        return JsonResponse({'bulundu': False})


@login_required
def hizli_stok_ekle(request, urun_id):
    if request.method != 'POST':
        return JsonResponse({'basarili': False}, status=405)
    urun = get_object_or_404(Urun, id=urun_id)
    urun.stok_miktari += 1
    urun.save()
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
        return JsonResponse({'basarili': False, 'hata': 'Ürün adı ve kategori zorunlu.'}, status=400)

    if barkod_no and Barkod.objects.filter(barkod_no=barkod_no).exists():
        return JsonResponse({'basarili': False, 'hata': 'Bu barkod zaten kayıtlı.'}, status=400)

    kategori = get_object_or_404(Kategori, id=kategori_id)

    with transaction.atomic():
        urun = Urun.objects.create(
            ad=ad, kategori=kategori,
            alis_fiyati=alis_fiyati, satis_fiyati=satis_fiyati,
            stok_miktari=stok_miktari,
        )
        if barkod_no:
            Barkod.objects.create(urun=urun, barkod_no=barkod_no)
        if int(stok_miktari) > 0:
            StokHareketi.objects.create(urun=urun, hareket_tipi='giris', miktar=stok_miktari, aciklama='Hızlı ekleme ekranı')

    return JsonResponse({'basarili': True, 'urun_id': urun.id, 'ad': urun.ad, 'kategori_id': kategori.id})
