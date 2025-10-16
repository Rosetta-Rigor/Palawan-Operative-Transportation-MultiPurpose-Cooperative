from django.contrib import admin
from .models import User, Member, Vehicle, Batch, Document, DocumentEntry

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'email', 'phone_number', 'role', 'id_image')
    search_fields = ('username', 'full_name', 'email', 'phone_number')
    list_filter = ('role',)

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'batch', 'batch_monitoring_number', 'is_dormant', 'user_account')
    search_fields = ('full_name',)
    list_filter = ('batch', 'is_dormant')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'make_brand', 'year_model', 'color', 'member')
    search_fields = ('plate_number', 'make_brand', 'engine_number', 'chassis_number')
    list_filter = ('body_type', 'year_model', 'color')

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('number', 'created_by')
    search_fields = ('number',)
    list_filter = ('created_by',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('tin', 'vehicle')
    search_fields = ('tin',)
    list_filter = ('vehicle',)

@admin.register(DocumentEntry)
class DocumentEntryAdmin(admin.ModelAdmin):
    list_display = ('document', 'renewal_date')
    search_fields = ('document__tin',)
    list_filter = ('renewal_date',)
