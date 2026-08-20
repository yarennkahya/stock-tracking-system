from django.contrib import admin
from .models import Firma, Senet


class SenetInline(admin.TabularInline):
    model = Senet
    extra = 1


@admin.register(Firma)
class FirmaAdmin(admin.ModelAdmin):
    list_display = ('ad', 'telefon', 'aktif', 'bakiye')
    list_filter = ('aktif',)
    inlines = [SenetInline]


@admin.register(Senet)
class SenetAdmin(admin.ModelAdmin):
    list_display = ('firma', 'tip', 'tutar', 'vade_tarihi', 'durum', 'aktif')
    list_filter = ('tip', 'durum', 'aktif')
