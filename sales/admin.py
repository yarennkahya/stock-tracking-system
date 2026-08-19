from django.contrib import admin
from .models import Satis, SatisKalemi


class SatisKalemiInline(admin.TabularInline):
    model = SatisKalemi
    extra = 1


@admin.register(Satis)
class SatisAdmin(admin.ModelAdmin):
    list_display = ('id', 'satisi_yapan', 'toplam_tutar', 'odeme_yontemi', 'pos_islem_no', 'tarih')
    list_filter = ('odeme_yontemi',)
    inlines = [SatisKalemiInline]
