from rest_framework.routers import DefaultRouter

from .views import (
    AbonnementViewSet,
    AbonnementAgronomeViewSet,
)


router = DefaultRouter()

router.register(
    r"configurations",
    AbonnementViewSet,
    basename="configuration-abonnement"
)

router.register(
    r"agronomes",
    AbonnementAgronomeViewSet,
    basename="abonnement-agronome"
)


urlpatterns = router.urls