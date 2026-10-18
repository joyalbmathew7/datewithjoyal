
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Activity, Profile, OutfitCategory
from .serializers import (
    ActivitySerializer,
    ProfileSerializer,
    OutfitCategorySerializer,
)


@api_view(["GET"])
def health_check(request):
    return Response({"message": "Rent a Boyfriend API is working!"})


@api_view(["GET"])
def public_profile(request):
    profile = Profile.objects.filter(is_active=True).first()

    if not profile:
        return Response({"message": "Profile not found."}, status=404)

    serializer = ProfileSerializer(profile, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
def activity_list(request):
    activities = Activity.objects.filter(is_available=True)
    serializer = ActivitySerializer(
        activities,
        many=True,
        context={"request": request},
    )
    return Response(serializer.data)


@api_view(["GET"])
def outfit_catalog(request):
    categories = (
        OutfitCategory.objects
        .filter(is_active=True)
        .prefetch_related("items")
    )

    serializer = OutfitCategorySerializer(
        categories,
        many=True,
        context={"request": request},
    )

    return Response(serializer.data)
