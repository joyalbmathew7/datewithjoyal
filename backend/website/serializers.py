
from rest_framework import serializers
from .models import (
    Profile,
    ProfilePhoto,
    Activity,
    OutfitCategory,
    OutfitItem,
)


class ProfilePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePhoto
        fields = [
            "id",
            "image",
            "photo_type",
            "caption",
        ]


class ProfileSerializer(serializers.ModelSerializer):
    photos = ProfilePhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "name",
            "date_of_birth",
            "bio",
            "photos",
        ]


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = [
            "id",
            "name",
            "description",
            "image",
        ]


class OutfitItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutfitItem
        fields = [
            "id",
            "name",
            "image",
            "specifications",
            "display_order",
        ]


class OutfitCategorySerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = OutfitCategory
        fields = [
            "id",
            "name",
            "is_required",
            "display_order",
            "items",
        ]

    def get_items(self, category):
        available_items = category.items.filter(
            is_available=True
        ).order_by("display_order", "name")

        return OutfitItemSerializer(
            available_items,
            many=True,
            context=self.context,
        ).data
