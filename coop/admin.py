from django.contrib import admin
from .models import User, Member, Vehicle, Batch, Document, DocumentEntry, Announcement

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


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('short_message', 'created_by', 'created_at', 'recipient_count')
    search_fields = ('message', 'created_by__username', 'created_by__full_name')
    list_filter = ('created_at',)
    filter_horizontal = ('recipients',)
    readonly_fields = ('created_at',)

    def save_model(self, request, obj, form, change):
        # Ensure created_by is set to the admin/manager creating the announcement
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        # Optional: place to trigger notification dispatch (email/push) to recipients
        # Example placeholder:
        # from .notifications import send_announcement_to_users
        # send_announcement_to_users(obj, obj.recipients.all())

    def short_message(self, obj):
        return (obj.message[:60] + '...') if len(obj.message) > 60 else obj.message
    short_message.short_description = "Message"

    def recipient_count(self, obj):
        return obj.recipients.count()
    recipient_count.short_description = "Recipients"