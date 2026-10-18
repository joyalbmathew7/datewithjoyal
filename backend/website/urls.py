
from django.urls import path

from .views import (
    health_check,
    public_profile,
    activity_list,
    outfit_catalog,
)

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("profile/", public_profile, name="public-profile"),
    path("activities/", activity_list, name="activity-list"),
    path("outfits/", outfit_catalog, name="outfit-catalog"),
]
