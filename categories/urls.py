from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategorieViewSet,
    UniteVenteViewSet,
    MoyenPaiementViewSet,
)

unite_router = DefaultRouter()
unite_router.register(
    r"",
    UniteVenteViewSet,
    basename="unites",
)

paiement_router = DefaultRouter()
paiement_router.register(
    r"",
    MoyenPaiementViewSet,
    basename="paiements",
)

urlpatterns = [
    # Catégories
    path(
        "",
        CategorieViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="categories-list",
    ),
    path(
        "<int:pk>/",
        CategorieViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="categories-detail",
    ),

    # Unités
    path(
        "unites/",
        include(unite_router.urls),
    ),

    # Moyens de paiement
    path(
        "paiements/",
        include(paiement_router.urls),
    ),
]