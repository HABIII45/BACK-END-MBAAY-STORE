from django.urls import path

from .views import CreerCommandeView,SuiviCommandeView,ConfirmerReceptionCommandeView,MesCommandesAgronomeView,DetailCommandeAgronomeView, AvancerCommandeAgronomeView


urlpatterns = [
    path(
        "creer/",
        CreerCommandeView.as_view(),
        name="creer-commande"
    ),
    path(
        "suivi/<str:token_suivi>/",
        SuiviCommandeView.as_view(),
        name="suivi-commande"
    ),

    path(
        "suivi/<str:token_suivi>/reception/",
        ConfirmerReceptionCommandeView.as_view(),
        name="confirmer-reception"
    ),
     # ==========================================
    # COMMANDES AGRONOME
    # ==========================================

    path(
        "mes-commandes/",
        MesCommandesAgronomeView.as_view(),
        name="mes-commandes"
    ),

    path(
        "mes-commandes/<int:commande_id>/",
        DetailCommandeAgronomeView.as_view(),
        name="detail-commande-agronome"
    ),

    path(
        "mes-commandes/<int:commande_id>/avancer/",
        AvancerCommandeAgronomeView.as_view(),
        name="avancer-commande"
    ),
]