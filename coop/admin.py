from django.contrib import admin
from .models import Batch, Member, Vehicle


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("id", "number")
    search_fields = ("number",)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "gmail", "batch", "file_number", "renewal_date")
    list_filter = ("batch", "renewal_date")
    search_fields = ("name", "gmail", "file_number")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("id", "plate_number", "engine_number", "chassis_number", "make_brand", "body_type", "year_model", "series", "member")
    list_filter = ("make_brand", "year_model", "body_type")
    search_fields = ("plate_number", "engine_number", "chassis_number", "make_brand", "series")
