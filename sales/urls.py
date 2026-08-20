from django.urls import path

from . import views


urlpatterns = [
    path('satis/', views.satis_ekrani, name='satis_ekrani'),
    path('satislar/', views.satis_raporu, name='satis_raporu'),
    path('satis/urun-ara/', views.urun_ara, name='urun_ara'),
    path('satis/barkod-ekle/', views.sepete_barkod_ekle, name='sepete_barkod_ekle'),
    path('satis/sepete-ekle/<int:urun_id>/', views.sepete_urun_ekle, name='sepete_urun_ekle'),
    path('satis/sepet/<int:urun_id>/', views.sepet_kalemi_guncelle, name='sepet_kalemi_guncelle'),
    path('satis/sil/<int:urun_id>/', views.sepetten_cikar, name='sepetten_cikar'),
    path('satis/tamamla/', views.satisi_tamamla, name='satisi_tamamla'),
    path('satis/<int:satis_id>/', views.satis_detay, name='satis_detay'),
]
