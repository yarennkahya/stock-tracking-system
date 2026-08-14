from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from inventory.models import Urun, Barkod
from .models import Satis, SatisKalemi


@login_required
def satis_ekrani(request):
    sepet = request.session.get('sepet', {})
    urunler = []
    toplam = 0
    for urun_id, kalem in sepet.items():
        satir_toplam = kalem['miktar'] * float(kalem['birim_fiyat'])
        toplam += satir_toplam
        urunler.append({
            'urun_id': urun_id,
            'ad': kalem['ad'],
            'miktar': kalem['miktar'],
            'birim_fiyat': kalem['birim_fiyat'],
            'satir_toplam': satir_toplam,
        })
    return render(request, 'satis_ekrani.html', {'sepet_urunleri': urunler, 'toplam': toplam})


@login_required
def sepete_barkod_ekle(request, barkod_no):
    try:
        barkod = Barkod.objects.get(barkod_no=barkod_no)
        urun = barkod.urun
    except Barkod.DoesNotExist:
        return JsonResponse({'basarili': False, 'hata': 'Barkod bulunamadı'}, status=404)

    sepet = request.session.get('sepet', {})
    urun_id = str(urun.id)
    mevcut_miktar = sepet.get(urun_id, {}).get('miktar', 0)

    if mevcut_miktar + 1 > urun.stok_miktari:
        return JsonResponse({'basarili': False, 'hata': f'Yetersiz stok: {urun.ad} (stokta {urun.stok_miktari} adet var)'}, status=400)

    if urun_id in sepet:
        sepet[urun_id]['miktar'] += 1
    else:
        sepet[urun_id] = {'ad': urun.ad, 'miktar': 1, 'birim_fiyat': str(urun.satis_fiyati)}

    request.session['sepet'] = sepet
    return JsonResponse({'basarili': True, 'ad': urun.ad})


@login_required
def sepetten_cikar(request, urun_id):
    sepet = request.session.get('sepet', {})
    sepet.pop(str(urun_id), None)
    request.session['sepet'] = sepet
    return redirect('satis_ekrani')


@login_required
def satisi_tamamla(request):
    sepet = request.session.get('sepet', {})
    if not sepet:
        return redirect('satis_ekrani')

    with transaction.atomic():
        satis = Satis.objects.create(satisi_yapan=request.user, toplam_tutar=0)
        toplam = 0
        for urun_id, kalem in sepet.items():
            urun = get_object_or_404(Urun, id=urun_id)
            SatisKalemi.objects.create(
                satis=satis, urun=urun,
                miktar=kalem['miktar'], birim_fiyat=kalem['birim_fiyat'],
            )
            urun.stok_miktari -= kalem['miktar']
            urun.save()
            toplam += kalem['miktar'] * float(kalem['birim_fiyat'])

        satis.toplam_tutar = toplam
        satis.save()

    request.session['sepet'] = {}
    return redirect('satis_detay', satis_id=satis.id)


@login_required
def satis_detay(request, satis_id):
    satis = get_object_or_404(Satis, id=satis_id)
    return render(request, 'satis_detay.html', {'satis': satis})