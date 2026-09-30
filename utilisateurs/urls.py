from django.urls import path

from .views import AdminLoginView,VerificationEmailView,DemanderLienConnexionView,ConnexionParLienView



urlpatterns = [
    path(
        "admin/login/",
        AdminLoginView.as_view(),
        name="admin-login"
    ),
     path(
        "verification-email/<str:token>/",
        VerificationEmailView.as_view(),
        name="verification-email"
    ),
     path(
        "agronome/demander-lien/",
        DemanderLienConnexionView.as_view(),
        name="demander-lien-connexion"
    ),

    path(
        "agronome/connexion/<str:token>/",
        ConnexionParLienView.as_view(),
        name="connexion-par-lien"
    ),
]