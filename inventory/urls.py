from django.urls import path

from . import views


urlpatterns = [
    path('', views.ana_sayfa, name='ana_sayfa'),
    path('urun/ekle/', views.urun_ekle, name='urun_ekle'),
    path('urun/hizli-ekle/', views.hizli_urun_ekle, name='hizli_urun_ekle'),
    path('urun/<int:urun_id>/', views.urun_detay, name='urun_detay'),
    path('urun/<int:urun_id>/duzenle/', views.urun_duzenle, name='urun_duzenle'),
    path('barkod-tara/', views.barkod_tara, name='barkod_tara'),
    path('kategoriler/', views.kategori_listesi, name='kategori_listesi'),
    path('kategoriler/ana-ekle/', views.ana_kategori_ekle, name='ana_kategori_ekle'),
    path('kategoriler/<int:kategori_id>/duzenle/', views.kategori_duzenle, name='kategori_duzenle'),
    path('api/barkod/<str:barkod_no>/', views.barkod_sorgula, name='barkod_sorgula'),
    path('api/urunler/', views.urun_listesi_api, name='urun_listesi_api'),
    path('api/urun-kontrol/<str:barkod_no>/', views.barkod_kontrol, name='barkod_kontrol'),
    path('api/stok-artir/<int:urun_id>/', views.hizli_stok_ekle, name='hizli_stok_ekle'),
    path('api/urun-hizli-kaydet/', views.hizli_urun_kaydet, name='hizli_urun_kaydet'),
    path('api/kategoriler/<int:ana_kategori_id>/alt-kategoriler/', views.alt_kategoriler, name='alt_kategoriler'),
]
