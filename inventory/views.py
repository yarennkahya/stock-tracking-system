from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Q
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator

from .forms import AltKategoriFormu, KategoriFormu, UrunForm
from .models import Barkod, Kategori, StokHareketi, Urun


def _gecerli_kategori_id(deger):
    try:
        kategori_id = int(deger)
    except (TypeError, ValueError):
        return None
    return kategori_id if kategori_id > 0 else None


def _urunleri_filtrele(parametreler):
    urunler = Urun.objects.select_related('kategori__parent').all()
    ana_kategoriler = Kategori.objects.filter(parent__isnull=True).order_by('ad')

    arama = parametreler.get('arama', '').strip()
    ana_kategori_id = parametreler.get('ana_kategori', '').strip()
    alt_kategori_id = parametreler.get('alt_kategori', '').strip()
    stok_durumu = parametreler.get('stok_durumu', '')

    secili_ana_kategori = None
    if ana_kategori_id:
        secili_ana_kategori = ana_kategoriler.filter(pk=_gecerli_kategori_id(ana_kategori_id)).first()
        if secili_ana_kategori:
            urunler = urunler.filter(
                Q(kategori=secili_ana_kategori) | Q(kategori__parent=secili_ana_kategori)
            )
        else:
            ana_kategori_id = ''

    alt_kategoriler = Kategori.objects.none()
    if secili_ana_kategori:
        alt_kategoriler = secili_ana_kategori.alt_kategoriler.order_by('ad')
        if alt_kategori_id:
            secili_alt_kategori = alt_kategoriler.filter(pk=_gecerli_kategori_id(alt_kategori_id)).first()
            if secili_alt_kategori:
                urunler = urunler.filter(kategori=secili_alt_kategori)
            else:
                alt_kategori_id = ''

    if arama:
        urunler = urunler.filter(Q(ad__icontains=arama) | Q(barkodlar__barkod_no__icontains=arama)).distinct()

    if stok_durumu == 'kritik':
        urunler = urunler.filter(stok_miktari__lte=F('kritik_stok_seviyesi'))
    elif stok_durumu == 'yeterli':
        urunler = urunler.filter(stok_miktari__gt=F('kritik_stok_seviyesi'))
    else:
        stok_durumu = ''

    return urunler.order_by('ad'), {
        'ana_kategoriler': ana_kategoriler,
        'alt_kategoriler': alt_kategoriler,
        'arama': arama,
        'secili_ana_kategori_id': ana_kategori_id,
        'secili_alt_kategori_id': alt_kategori_id,
        'stok_durumu': stok_durumu,
    }


@login_required
def ana_sayfa(request):
    urunler, filtre_bilgileri = _urunleri_filtrele(request.GET)
    urun_sayfasi = Paginator(urunler, 20).get_page(request.GET.get('sayfa'))
    filtreler = request.GET.copy()
    filtreler.pop('sayfa', None)
    return render(request, 'ana_sayfa.html', {
        'urunler': urun_sayfasi,
        'filtre_sorgusu': filtreler.urlencode(),
        **filtre_bilgileri,
    })


@login_required
@require_GET
def urun_listesi_api(request):
    urunler, _ = _urunleri_filtrele(request.GET)
    sayfalayici = Paginator(urunler, 20)
    sayfa = sayfalayici.get_page(request.GET.get('sayfa'))
    return JsonResponse({
        'toplam_sonuc': sayfalayici.count,
        'urunler': [
            {
                'id': urun.id,
                'ad': urun.ad,
                'kategori': urun.kategori.tam_ad,
                'satis_fiyati': str(urun.satis_fiyati),
                'stok_miktari': urun.stok_miktari,
                'kritik_stokta': urun.stok_miktari <= urun.kritik_stok_seviyesi,
            }
            for urun in sayfa.object_list
        ],
        'sayfalama': {
            'sayfa': sayfa.number,
            'toplam_sayfa': sayfalayici.num_pages,
            'onceki_var': sayfa.has_previous(),
            'sonraki_var': sayfa.has_next(),
        },
    })


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
        with transaction.atomic():
            urun = form.save()
            barkod_no = form.cleaned_data.get('barkod_no')
            if barkod_no:
                Barkod.objects.create(urun=urun, barkod_no=barkod_no)
        messages.success(request, 'Ürün eklendi.')
        return redirect('urun_detay', urun_id=urun.id)
    return render(request, 'urun_ekle.html', {
        'form': form,
        'sayfa_basligi': 'Yeni Ürün Ekle',
        'sayfa_aciklamasi': 'Manuel olarak ya da barkod okutarak yeni ürün ekle',
        'submit_etiketi': 'Ürünü Kaydet',
    })


@login_required
def urun_duzenle(request, urun_id):
    urun = get_object_or_404(Urun, id=urun_id)
    form = UrunForm(request.POST or None, instance=urun)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            urun = form.save()
            barkod_no = form.cleaned_data['barkod_no']
            mevcut_barkod = urun.barkodlar.order_by('id').first()
            if barkod_no:
                if mevcut_barkod:
                    mevcut_barkod.barkod_no = barkod_no
                    mevcut_barkod.save(update_fields=['barkod_no'])
                else:
                    Barkod.objects.create(urun=urun, barkod_no=barkod_no)
            else:
                urun.barkodlar.all().delete()
        messages.success(request, 'Ürün bilgileri güncellendi.')
        return redirect('urun_detay', urun_id=urun.id)
    return render(request, 'urun_ekle.html', {
        'form': form,
        'urun': urun,
        'sayfa_basligi': 'Ürünü Düzenle',
        'sayfa_aciklamasi': f'{urun.ad} ürününün bilgilerini güncelleyin',
        'submit_etiketi': 'Değişiklikleri Kaydet',
    })


@login_required
def kategori_listesi(request):
    ana_kategoriler = Kategori.objects.filter(parent__isnull=True).order_by('ad')
    secili_ana_kategori_id = request.POST.get('ana_kategori') or request.GET.get('ana_kategori')
    secili_ana_kategori = None
    if secili_ana_kategori_id:
        secili_ana_kategori = ana_kategoriler.filter(pk=_gecerli_kategori_id(secili_ana_kategori_id)).first()

    form = AltKategoriFormu(request.POST or None)
    if request.method == 'POST':
        if not secili_ana_kategori:
            messages.error(request, 'Önce geçerli bir ana kategori seçin.')
        elif form.is_valid():
            alt_kategori = form.save(commit=False)
            alt_kategori.parent = secili_ana_kategori
            alt_kategori.save()
            messages.success(request, f'{secili_ana_kategori.ad} için alt kategori eklendi.')
            return redirect(f'{reverse("kategori_listesi")}?ana_kategori={secili_ana_kategori.id}')

    alt_kategoriler = Kategori.objects.none()
    if secili_ana_kategori:
        alt_kategoriler = secili_ana_kategori.alt_kategoriler.order_by('ad')
    return render(request, 'kategori_listesi.html', {
        'form': form,
        'ana_kategoriler': ana_kategoriler,
        'secili_ana_kategori': secili_ana_kategori,
        'alt_kategoriler': alt_kategoriler,
    })


@login_required
def ana_kategori_ekle(request):
    form = KategoriFormu(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        kategori = form.save(commit=False)
        kategori.parent = None
        kategori.save()
        messages.success(request, f'{kategori.ad} ana kategorisi eklendi.')
        return redirect(f'{reverse("kategori_listesi")}?ana_kategori={kategori.id}')
    return render(request, 'kategori_formu.html', {
        'form': form,
        'sayfa_basligi': 'Ana Kategori Ekle',
        'sayfa_aciklamasi': 'Ürün gruplarını düzenli yönetmek için yeni bir ana kategori oluşturun.',
        'submit_etiketi': 'Ana Kategoriyi Kaydet',
    })


@login_required
def kategori_duzenle(request, kategori_id):
    kategori = get_object_or_404(Kategori, id=kategori_id)
    form = KategoriFormu(request.POST or None, instance=kategori)
    if request.method == 'POST' and form.is_valid():
        kategori = form.save()
        ana_kategori_id = kategori.parent_id or kategori.id
        messages.success(request, 'Kategori bilgileri güncellendi.')
        return redirect(f'{reverse("kategori_listesi")}?ana_kategori={ana_kategori_id}')
    return render(request, 'kategori_formu.html', {
        'form': form,
        'kategori': kategori,
        'sayfa_basligi': 'Kategori Düzenle',
        'sayfa_aciklamasi': f'{kategori.tam_ad} kategorisinin adını ve açıklamasını güncelleyin.',
        'submit_etiketi': 'Değişiklikleri Kaydet',
        'geri_donus_url': f'{reverse("kategori_listesi")}?ana_kategori={kategori.parent_id or kategori.id}',
    })


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
