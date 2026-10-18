from django.contrib import admin
from .models import (
    Availability,
    Booking,
    BookingOutfitSelection,
    District,
)
from django.utils.html import format_html


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "start_time",
        "end_time",
        "is_available",
        "display_districts",
    )
    list_filter = ("date", "is_available", "districts")
    ordering = ("date", "start_time")
    filter_horizontal = ("districts",)

    @admin.display(description="Districts")
    def display_districts(self, obj):
        return ", ".join(
            district.name for district in obj.districts.all()
        )


class BookingOutfitSelectionInline(admin.TabularInline):
    model = BookingOutfitSelection
    extra = 0
    readonly_fields = (
        "item_name",
        "item_specifications",
        "image_preview",
    )
    fields = (
        "item_name",
        "item_specifications",
        "image_preview",
    )

    @admin.display(description="Outfit image")
    def image_preview(self, obj):
        if obj and obj.item_image:
            return format_html(
                '<img src="{}" width="100" style="object-fit: contain;" />',
                obj.item_image,
            )
        return "No image"

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "customer_phone",
        "availability",
        "district",
        "total_amount",
        "status",
    )
    list_filter = ("status", "district")
    search_fields = ("customer_name", "customer_phone")
    filter_horizontal = ("activities",)
    inlines = [BookingOutfitSelectionInline]