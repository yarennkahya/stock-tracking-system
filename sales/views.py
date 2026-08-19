from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from inventory.models import Barkod, StokHareketi, Urun
from .models import Satis, SatisKalemi


def _sepet_ozeti(sepet):
    kalemler = []
    toplam = Decimal('0')
    toplam_adet = 0
    for urun_id, kalem in sepet.items():
        miktar = int(kalem['miktar'])
        birim_fiyat = Decimal(str(kalem['birim_fiyat']))
        satir_toplam = birim_fiyat * miktar
        toplam += satir_toplam
        toplam_adet += miktar
        kalemler.append({
            'urun_id': int(urun_id),
            'ad': kalem['ad'],
            'miktar': miktar,
            'birim_fiyat': str(birim_fiyat),
            'satir_toplam': str(satir_toplam),
        })
    return {'kalemler': kalemler, 'toplam': str(toplam), 'toplam_adet': toplam_adet}


def _sepete_urun_ekle(request, urun):
    sepet = request.session.get('sepet', {})
    urun_id = str(urun.id)
    mevcut_miktar = sepet.get(urun_id, {}).get('miktar', 0)

    if mevcut_miktar + 1 > urun.stok_miktari:
        return None, f'Yetersiz stok: {urun.ad} (stokta {urun.stok_miktari} adet var).'

    if urun_id in sepet:
        sepet[urun_id]['miktar'] += 1
    else:
        sepet[urun_id] = {
            'ad': urun.ad,
            'miktar': 1,
            'birim_fiyat': str(urun.satis_fiyati),
        }
    request.session['sepet'] = sepet
    return _sepet_ozeti(sepet), None


@login_required
def satis_ekrani(request):
    sepet = request.session.get('sepet', {})
    return render(request, 'satis_ekrani.html', {'sepet': _sepet_ozeti(sepet)})


@login_required
@require_GET
def urun_ara(request):
    sorgu = request.GET.get('q', '').strip()
    if not sorgu:
        return JsonResponse({'sonuclar': [], 'tam_barkod_urun_id': None})

    urunler = (
        Urun.objects.filter(Q(ad__icontains=sorgu) | Q(barkodlar__barkod_no__icontains=sorgu))
        .select_related('kategori')
        .prefetch_related('barkodlar')
        .distinct()[:12]
    )
    tam_barkod = Barkod.objects.filter(barkod_no=sorgu).values_list('urun_id', flat=True).first()
    return JsonResponse({
        'tam_barkod_urun_id': tam_barkod,
        'sonuclar': [
            {
                'id': urun.id,
                'ad': urun.ad,
                'kategori': urun.kategori.ad,
                'satis_fiyati': str(urun.satis_fiyati),
                'stok_miktari': urun.stok_miktari,
                'barkodlar': list(urun.barkodlar.values_list('barkod_no', flat=True)),
            }
            for urun in urunler
        ],
    })


@login_required
@require_POST
def sepete_barkod_ekle(request):
    barkod_no = request.POST.get('barkod_no', '').strip()
    barkod = Barkod.objects.select_related('urun').filter(barkod_no=barkod_no).first()
    if not barkod:
        return JsonResponse({'basarili': False, 'hata': 'Barkod bulunamadı.'}, status=404)

    sepet, hata = _sepete_urun_ekle(request, barkod.urun)
    if hata:
        return JsonResponse({'basarili': False, 'hata': hata}, status=400)
    return JsonResponse({'basarili': True, 'sepet': sepet})


@login_required
@require_POST
def sepete_urun_ekle(request, urun_id):
    urun = get_object_or_404(Urun, id=urun_id)
    sepet, hata = _sepete_urun_ekle(request, urun)
    if hata:
        return JsonResponse({'basarili': False, 'hata': hata}, status=400)
    return JsonResponse({'basarili': True, 'sepet': sepet})


@login_required
@require_POST
def sepet_kalemi_guncelle(request, urun_id):
    sepet = request.session.get('sepet', {})
    urun_id_str = str(urun_id)
    if urun_id_str not in sepet:
        return JsonResponse({'basarili': False, 'hata': 'Ürün sepette bulunamadı.'}, status=404)

    islem = request.POST.get('islem')
    if islem == 'artir':
        urun = get_object_or_404(Urun, id=urun_id)
        guncel_sepet, hata = _sepete_urun_ekle(request, urun)
        if hata:
            return JsonResponse({'basarili': False, 'hata': hata}, status=400)
        return JsonResponse({'basarili': True, 'sepet': guncel_sepet})

    if islem == 'azalt':
        sepet[urun_id_str]['miktar'] -= 1
        if sepet[urun_id_str]['miktar'] <= 0:
            sepet.pop(urun_id_str)
    elif islem == 'sil':
        sepet.pop(urun_id_str)
    else:
        return JsonResponse({'basarili': False, 'hata': 'Geçersiz sepet işlemi.'}, status=400)

    request.session['sepet'] = sepet
    return JsonResponse({'basarili': True, 'sepet': _sepet_ozeti(sepet)})


@login_required
def sepetten_cikar(request, urun_id):
    sepet = request.session.get('sepet', {})
    sepet.pop(str(urun_id), None)
    request.session['sepet'] = sepet
    return redirect('satis_ekrani')


@login_required
@require_POST
def satisi_tamamla(request):
    sepet = request.session.get('sepet', {})
    if not sepet:
        return redirect('satis_ekrani')

    odeme_yontemi = request.POST.get('odeme_yontemi', 'nakit')
    if odeme_yontemi not in dict(Satis.ODEME_YONTEMLERI):
        messages.error(request, 'Geçerli bir ödeme yöntemi seçin.')
        return redirect('satis_ekrani')

    pos_islem_no = ''
    if odeme_yontemi == 'kart':
        pos_islem_no = request.POST.get('pos_islem_no', '').strip()
        if request.POST.get('pos_onay') != '1' or not pos_islem_no.startswith('DEMO-POS-'):
            messages.error(request, 'Demo POS ödeme onayı alınamadı. Sepetiniz korunuyor.')
            return redirect('satis_ekrani')

    with transaction.atomic():
        urunler = {}
        for urun_id, kalem in sepet.items():
            urun = get_object_or_404(Urun.objects.select_for_update(), id=urun_id)
            if kalem['miktar'] > urun.stok_miktari:
                messages.error(request, f'{urun.ad} için yeterli stok kalmadı.')
                return redirect('satis_ekrani')
            urunler[urun_id] = urun

        satis = Satis.objects.create(
            satisi_yapan=request.user,
            toplam_tutar=Decimal('0'),
            odeme_yontemi=odeme_yontemi,
            pos_islem_no=pos_islem_no,
        )
        toplam = Decimal('0')
        for urun_id, kalem in sepet.items():
            urun = urunler[urun_id]
            birim_fiyat = Decimal(str(kalem['birim_fiyat']))
            miktar = kalem['miktar']
            SatisKalemi.objects.create(satis=satis, urun=urun, miktar=miktar, birim_fiyat=birim_fiyat)
            urun.stok_miktari -= miktar
            urun.save(update_fields=['stok_miktari'])
            StokHareketi.objects.create(urun=urun, hareket_tipi='cikis', miktar=miktar, aciklama=f'Satış #{satis.id}')
            toplam += birim_fiyat * miktar

        satis.toplam_tutar = toplam
        satis.save(update_fields=['toplam_tutar'])

    request.session['sepet'] = {}
    return redirect('satis_detay', satis_id=satis.id)


@login_required
def satis_detay(request, satis_id):
    satis = get_object_or_404(Satis, id=satis_id)
    return render(request, 'satis_detay.html', {'satis': satis})
