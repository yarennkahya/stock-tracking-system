from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Urun, Barkod


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