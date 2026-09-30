from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InformationAgricoleViewSet


router = DefaultRouter()

router.register(
    "",
    InformationAgricoleViewSet,
    basename="informations-agricoles"
)


urlpatterns = [
    path("", include(router.urls)),
]