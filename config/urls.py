"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from inventory import views
from sales import views as sales_views
from accounts import views as accounts_views
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('giris/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('cikis/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.ana_sayfa, name='ana_sayfa'),
    path('urun/<int:urun_id>/', views.urun_detay, name='urun_detay'),
    path('barkod-tara/', views.barkod_tara, name='barkod_tara'),
    path('api/barkod/<str:barkod_no>/', views.barkod_sorgula, name='barkod_sorgula'),
    path('i18n/', include('django.conf.urls.i18n')),

    path('satis/', sales_views.satis_ekrani, name='satis_ekrani'),
    path('satis/barkod-ekle/<str:barkod_no>/', sales_views.sepete_barkod_ekle, name='sepete_barkod_ekle'),
    path('satis/sil/<int:urun_id>/', sales_views.sepetten_cikar, name='sepetten_cikar'),
    path('satis/tamamla/', sales_views.satisi_tamamla, name='satisi_tamamla'),
    path('satis/<int:satis_id>/', sales_views.satis_detay, name='satis_detay'),
    path('firmalar/', accounts_views.firma_listesi, name='firma_listesi'),
    path('urun/ekle/', views.urun_ekle, name='urun_ekle'),
    path('senet-takip/', accounts_views.senet_takip, name='senet_takip'),
    path('urun/hizli-ekle/', views.hizli_urun_ekle, name='hizli_urun_ekle'),
path('api/urun-kontrol/<str:barkod_no>/', views.barkod_kontrol, name='barkod_kontrol'),
path('api/stok-artir/<int:urun_id>/', views.hizli_stok_ekle, name='hizli_stok_ekle'),
path('api/urun-hizli-kaydet/', views.hizli_urun_kaydet, name='hizli_urun_kaydet'),
    ]