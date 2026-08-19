from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from inventory.models import Barkod, StokHareketi, Urun
from .models import Satis, SatisKalemi


AY_ADLARI = ('Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara')


def _tarih_oku(deger):
    try:
        return date.fromisoformat(deger)
    except (TypeError, ValueError):
        return None


def _ay_ilerlet(tarih):
    if tarih.month == 12:
        return tarih.replace(year=tarih.year + 1, month=1, day=1)
    return tarih.replace(month=tarih.month + 1, day=1)


def _ciro_grafigi(satislar, baslangic, bitis):
    gun_sayisi = (bitis - baslangic).days + 1
    aylik_gosterim = gun_sayisi > 62
    aktif_saat_dilimi = timezone.get_current_timezone()

    if aylik_gosterim:
        satirlar = (
            satislar.annotate(donem=TruncMonth('tarih', tzinfo=aktif_saat_dilimi))
            .values('donem').annotate(toplam=Sum('toplam_tutar')).order_by('donem')
        )
        toplamlar = {satir['donem'].date().replace(day=1): satir['toplam'] for satir in satirlar}
        donemler = []
        mevcut = baslangic.replace(day=1)
        son = bitis.replace(day=1)
        while mevcut <= son:
            donemler.append(mevcut)
            mevcut = _ay_ilerlet(mevcut)
        etiket = 'Aylık ciro'
    else:
        satirlar = (
            satislar.annotate(donem=TruncDate('tarih', tzinfo=aktif_saat_dilimi))
            .values('donem').annotate(toplam=Sum('toplam_tutar')).order_by('donem')
        )
        toplamlar = {satir['donem']: satir['toplam'] for satir in satirlar}
        donemler = [baslangic + timedelta(days=gun) for gun in range(gun_sayisi)]
        etiket = 'Günlük ciro'

    en_yuksek = max(toplamlar.values(), default=Decimal('0'))
    grafik = []
    for donem in donemler:
        toplam = toplamlar.get(donem, Decimal('0'))
        oran = 0 if not en_yuksek else max(5, round(float(toplam / en_yuksek * 100)))
        if aylik_gosterim:
            donem_etiketi = f'{AY_ADLARI[donem.month - 1]} {str(donem.year)[2:]}'
        else:
            donem_etiketi = donem.strftime('%d.%m')
        grafik.append({'etiket': donem_etiketi, 'toplam': toplam, 'oran': oran})
    return grafik, etiket


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
def satis_raporu(request):
    bugun = timezone.localdate()
    donem = request.GET.get('donem', 'ay')
    baslangic_degeri = request.GET.get('baslangic', '')
    bitis_degeri = request.GET.get('bitis', '')

    if donem == 'gun':
        baslangic = bitis = bugun
    elif donem == 'yil':
        baslangic, bitis = date(bugun.year, 1, 1), bugun
    elif donem == 'ozel':
        baslangic = _tarih_oku(baslangic_degeri)
        bitis = _tarih_oku(bitis_degeri)
        if not baslangic or not bitis:
            messages.warning(request, 'Özel tarih aralığı için başlangıç ve bitiş tarihi girin.')
            baslangic, bitis, donem = bugun.replace(day=1), bugun, 'ay'
        elif baslangic > bitis:
            baslangic, bitis = bitis, baslangic
    else:
        baslangic, bitis, donem = bugun.replace(day=1), bugun, 'ay'

    satislar = Satis.objects.select_related('satisi_yapan').filter(tarih__date__range=(baslangic, bitis))
    ozet = satislar.aggregate(
        ciro=Sum('toplam_tutar'),
        satis_adedi=Count('id'),
        nakit_toplami=Sum('toplam_tutar', filter=Q(odeme_yontemi='nakit')),
        kart_toplami=Sum('toplam_tutar', filter=Q(odeme_yontemi='kart')),
    )
    ciro = ozet['ciro'] or Decimal('0.00')
    satis_adedi = ozet['satis_adedi'] or 0
    grafik, grafik_basligi = _ciro_grafigi(satislar, baslangic, bitis)

    filtreler = request.GET.copy()
    filtreler.pop('sayfa', None)
    sayfalanmis_satislar = Paginator(satislar.order_by('-tarih'), 20).get_page(request.GET.get('sayfa'))
    return render(request, 'satis_raporu.html', {
        'satislar': sayfalanmis_satislar,
        'donem': donem,
        'baslangic': baslangic,
        'bitis': bitis,
        'baslangic_degeri': baslangic_degeri,
        'bitis_degeri': bitis_degeri,
        'ciro': ciro,
        'satis_adedi': satis_adedi,
        'ortalama_sepet': ciro / satis_adedi if satis_adedi else Decimal('0.00'),
        'nakit_toplami': ozet['nakit_toplami'] or Decimal('0.00'),
        'kart_toplami': ozet['kart_toplami'] or Decimal('0.00'),
        'grafik': grafik,
        'grafik_basligi': grafik_basligi,
        'filtre_sorgusu': filtreler.urlencode(),
    })


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
