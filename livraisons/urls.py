from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ModeLivraisonViewSet,
    ParametreLivraisonViewSet,
    ConfigurationLivraisonBoutiqueViewSet,
    ContactLivreurViewSet,
)


router = DefaultRouter()

router.register(
    r"modes",
    ModeLivraisonViewSet,
    basename="modes-livraison"
)

router.register(
    r"parametres",
    ParametreLivraisonViewSet,
    basename="parametres-livraison"
)

router.register(
    r"configurations",
    ConfigurationLivraisonBoutiqueViewSet,
    basename="configurations-livraison"
)

router.register(
    r"livreurs",
    ContactLivreurViewSet,
    basename="contacts-livreurs"
)


urlpatterns = [
    path("", include(router.urls)),
]