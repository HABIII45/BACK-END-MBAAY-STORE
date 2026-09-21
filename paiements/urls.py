from django.urls import path

from .views import CreerPaiementAbonnementView,PaydunyaIPNView


urlpatterns = [
    path(
        "abonnement/",
        CreerPaiementAbonnementView.as_view(),
        name="creer-paiement-abonnement",
    ),
    path(
        "paydunya/ipn/",
        PaydunyaIPNView.as_view(),
        name="paydunya-ipn",
    ),
]