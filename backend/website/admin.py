
from django.contrib import admin
from .models import (
    Profile,
    ProfilePhoto,
    Activity,
    SiteSettings,
    OutfitCategory,
    OutfitItem,
)


class ProfilePhotoInline(admin.TabularInline):
    model = ProfilePhoto
    extra = 1


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "date_of_birth", "is_active")
    inlines = [ProfilePhotoInline]


@admin.register(ProfilePhoto)
class ProfilePhotoAdmin(admin.ModelAdmin):
    list_display = ("profile", "photo_type", "caption", "is_visible")
    list_filter = ("photo_type", "is_visible")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "is_available", "created_at")
    list_filter = ("is_available",)
    search_fields = ("name",)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "hourly_rate",
        "minimum_booking_hours",
        "booking_gap_minutes",
    )


@admin.register(OutfitCategory)
class OutfitCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_required", "is_active", "display_order")
    list_filter = ("is_required", "is_active")
    search_fields = ("name",)


@admin.register(OutfitItem)
class OutfitItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "is_available",
        "display_order",
    )
    list_filter = ("category", "is_available")
    search_fields = ("name",)
