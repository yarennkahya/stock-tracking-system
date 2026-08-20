from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import SifreSifirlamaFormu


urlpatterns = [
    path('giris/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('cikis/', auth_views.LogoutView.as_view(), name='logout'),
    path('uye-ol/', views.uye_ol, name='uye_ol'),
    path('hesap-ayarlari/', views.hesap_ayarlari, name='hesap_ayarlari'),
    path(
        'sifremi-unuttum/',
        auth_views.PasswordResetView.as_view(
            form_class=SifreSifirlamaFormu,
            template_name='password_reset_form.html',
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'sifremi-unuttum/tamam/',
        auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
        name='password_reset_done',
    ),
    path(
        'sifre-yenile/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'sifre-yenile/tamam/',
        auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
        name='password_reset_complete',
    ),
    path('firmalar/', views.firma_listesi, name='firma_listesi'),
    path('firmalar/ekle/', views.firma_ekle, name='firma_ekle'),
    path('firmalar/<int:firma_id>/duzenle/', views.firma_duzenle, name='firma_duzenle'),
    path('firmalar/<int:firma_id>/durum/', views.firma_durum_degistir, name='firma_durum_degistir'),
    path('senet-takip/', views.senet_takip, name='senet_takip'),
    path('senet-takip/ekle/', views.senet_ekle, name='senet_ekle'),
    path('senet-takip/<int:senet_id>/duzenle/', views.senet_duzenle, name='senet_duzenle'),
    path('senet-takip/<int:senet_id>/durum/', views.senet_durum_degistir, name='senet_durum_degistir'),
    path('senet-takip/<int:senet_id>/sil/', views.senet_sil, name='senet_sil'),
]
