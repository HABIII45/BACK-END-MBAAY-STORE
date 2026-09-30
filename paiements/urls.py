from django.urls import path

from .views import CreerPaiementAbonnementView,PaydunyaIPNView,ActiverEssaiGratuitView,CreerPaiementCommandeView,CompteReversementView, MonAbonnementView



urlpatterns = [
    path(
        "abonnement/",
        CreerPaiementAbonnementView.as_view(),
        name="creer-paiement-abonnement",
    ),
     path(
        "abonnement/essai/",
        ActiverEssaiGratuitView.as_view(),
        name="activer-essai-gratuit",
    ),
    path(
        "paydunya/ipn/",
        PaydunyaIPNView.as_view(),
        name="paydunya-ipn",
    ),
     path(
        "commande/",
        CreerPaiementCommandeView.as_view(),
        name="creer-paiement-commande"
    ),
     
     



    path(
        "compte-reversement/",
        CompteReversementView.as_view(),
        name="compte-reversement",
    ),
    path(
    "abonnement/mon-abonnement/",
    MonAbonnementView.as_view(),
    name="mon-abonnement",
    ),
]