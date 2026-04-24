from django.contrib import admin
from .models import User, Member, Vehicle, Batch, Document, DocumentEntry, Announcement, PaymentYear, PaymentType, PaymentEntry


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'email', 'phone_number', 'role', 'id_image')
    search_fields = ('username', 'full_name', 'email', 'phone_number')
    list_filter = ('role',)

    def has_module_permission(self, request):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'superadmin'

    def has_view_permission(self, request, obj=None):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'superadmin'

    def has_add_permission(self, request):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'superadmin'

    def has_change_permission(self, request, obj=None):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'superadmin'

    def has_delete_permission(self, request, obj=None):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'superadmin'

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'batch', 'batch_monitoring_number', 'is_dormant', 'user_account')
    search_fields = ('full_name', 'batch__number', 'batch_monitoring_number', 'phone_number', 'email')
    list_filter = ('batch', 'is_dormant')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'make_brand', 'year_model', 'color', 'member')
    search_fields = ('plate_number', 'make_brand', 'engine_number', 'chassis_number', 'member__full_name')
    list_filter = ('body_type', 'year_model', 'color')

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('number', 'created_by')
    search_fields = ('number', 'created_by__username', 'created_by__full_name')
    list_filter = ('created_by',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('mv_file_no', 'vehicle')
    search_fields = ('mv_file_no', 'vehicle__plate_number', 'vehicle__make_brand')
    list_filter = ('vehicle',)

@admin.register(DocumentEntry)
class DocumentEntryAdmin(admin.ModelAdmin):
    list_display = ('document', 'renewal_date')
    search_fields = ('document__mv_file_no', 'document__vehicle__plate_number')
    list_filter = ('renewal_date',)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('short_message', 'created_by', 'created_at', 'recipient_count')
    search_fields = ('message', 'created_by__username', 'created_by__full_name', 'recipients__username', 'recipients__full_name')
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

@admin.register(PaymentYear)
class PaymentYearAdmin(admin.ModelAdmin):
    list_display = ('year',)
    search_fields = ('year',)
@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'payment_type', 'amount', 'frequency', 'year')
    search_fields = ('name', 'year__year', 'payment_type')
    list_filter = ('payment_type', 'year')
@admin.register(PaymentEntry)
class PaymentEntryAdmin(admin.ModelAdmin):
    list_display = ('payment_type', 'member', 'month', 'amount_paid', 'recorded_at', 'recorded_by')
    search_fields = ('payment_type__name', 'member__full_name', 'month', 'amount_paid', 'recorded_by__username')
    list_filter = ('payment_type', 'month', 'recorded_at')

    def get_queryset(self, request):
            qs = super().get_queryset(request)
            # Only show entries that were recorded by a user (not system-generated)
            return qs.filter(recorded_by__isnull=False)