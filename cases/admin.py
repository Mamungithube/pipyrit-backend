from django.contrib import admin

# Register your models here.

from .models import CaseType, ImmigrationCase, CaseDocument
@admin.register(CaseType)
class CaseTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
@admin.register(ImmigrationCase)
class ImmigrationCaseAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'user', 'case_type', 'status', 'last_update')
    search_fields = ('title', 'user__email', 'case_type__name')
    list_filter = ('case_type', 'status')
    ordering = ('-last_update',)
@admin.register(CaseDocument)
class CaseDocumentAdmin(admin.ModelAdmin):
    list_display = ('case', 'file', 'uploaded_at')
    search_fields = ('case__title', 'case__user__email')
    ordering = ('-uploaded_at',)