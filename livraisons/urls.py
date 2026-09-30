from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ModeLivraisonViewSet,
    ParametreLivraisonViewSet,
    ConfigurationLivraisonBoutiqueViewSet,
    ContactLivreurViewSet,
    TarifLivraisonDistanceViewSet,
    LivraisonBoutiquePubliqueView,
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
router.register(
    r"tarifs-distance",
    TarifLivraisonDistanceViewSet,
    basename="tarif-distance"
)


urlpatterns = [
    path(
        "boutiques/<int:boutique_id>/",
        LivraisonBoutiquePubliqueView.as_view(),
        name="livraison-boutique-publique"
    ),

    path("", include(router.urls)),
]