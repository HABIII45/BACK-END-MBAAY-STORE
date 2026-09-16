from rest_framework.routers import DefaultRouter
from .views import BoutiqueViewSet

router = DefaultRouter()

router.register(
    r"boutiques",
    BoutiqueViewSet,
    basename="boutique"
)

urlpatterns = router.urls
