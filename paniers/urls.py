from django.urls import path

from .views import (
    PanierView,
    AjouterAuPanierView,
    ModifierQuantitePanierView,
    SupprimerLignePanierView,
    ViderPanierView,
)


urlpatterns = [
    path(
        "",
        PanierView.as_view(),
        name="mon-panier",
    ),

    path(
        "ajouter/",
        AjouterAuPanierView.as_view(),
        name="ajouter-au-panier",
    ),

    path(
        "lignes/<int:ligne_id>/",
        ModifierQuantitePanierView.as_view(),
        name="modifier-quantite-panier",
    ),

    path(
        "lignes/<int:ligne_id>/supprimer/",
        SupprimerLignePanierView.as_view(),
        name="supprimer-ligne-panier",
    ),

    path(
        "vider/",
        ViderPanierView.as_view(),
        name="vider-panier",
    ),
]