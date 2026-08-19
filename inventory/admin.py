from django.contrib import admin
from django import forms
from django.db import models
from .models import Kategori, Urun, Barkod, StokHareketi


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ('ad', 'parent')
    list_filter = ('parent',)
    search_fields = ('ad',)


@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ('ad', 'kategori', 'satis_fiyati', 'stok_miktari', 'kritik_stok_seviyesi')
    list_filter = ('kategori',)
    search_fields = ('ad',)
    formfield_overrides = {
        models.DecimalField: {'widget': forms.NumberInput(attrs={'step': '1', 'min': '0'})},
    }


@admin.register(Barkod)
class BarkodAdmin(admin.ModelAdmin):
    list_display = ('barkod_no', 'urun')
    search_fields = ('barkod_no',)


@admin.register(StokHareketi)
class StokHareketiAdmin(admin.ModelAdmin):
    list_display = ('urun', 'hareket_tipi', 'miktar', 'tarih')
    list_filter = ('hareket_tipi',)
