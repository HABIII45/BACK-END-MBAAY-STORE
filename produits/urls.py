from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
   
    ProduitViewSet,
    ProduitPublicListView,
)


router = DefaultRouter()


router.register(
    r"mes-produits",
    ProduitViewSet,
    basename="mes-produits"
)


urlpatterns = [
    path("", include(router.urls)),
    path(
        "liste/",
        ProduitPublicListView.as_view(),
        name="produits-publics"
    ),
]