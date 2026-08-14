from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Urun


@login_required
def ana_sayfa(request):
    urunler = Urun.objects.all()
    return render(request, 'ana_sayfa.html', {'urunler': urunler})


@login_required
def urun_detay(request, urun_id):
    urun = get_object_or_404(Urun, id=urun_id)
    return render(request, 'urun_detay.html', {'urun': urun})