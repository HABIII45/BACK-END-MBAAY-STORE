from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Abonnement, AbonnementAgronome
from .serializers import (
    AbonnementSerializer,
    AbonnementAgronomeSerializer,
)


class AbonnementViewSet(viewsets.ModelViewSet):
    """
    Gestion de la configuration générale de l'abonnement MBAAY.

    Admin :
        - peut consulter
        - peut créer
        - peut modifier
        - peut supprimer

    Agronome :
        - peut uniquement consulter la configuration active
    """

    serializer_class = AbonnementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Abonnement.objects.all().order_by("-date_modification")

    def perform_create(self, serializer):
        # Seul l'administrateur peut créer une configuration
        if self.request.user.role != "ADMIN":
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Seul l'administrateur peut créer une configuration d'abonnement."
            )

        serializer.save()

    def perform_update(self, serializer):
        # Seul l'administrateur peut modifier
        if self.request.user.role != "ADMIN":
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Seul l'administrateur peut modifier la configuration d'abonnement."
            )

        serializer.save()

    def perform_destroy(self, instance):
        # Seul l'administrateur peut supprimer
        if self.request.user.role != "ADMIN":
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Seul l'administrateur peut supprimer la configuration d'abonnement."
            )

        instance.delete()


class AbonnementAgronomeViewSet(viewsets.ModelViewSet):
    """
    Gestion des abonnements individuels des agronomes.

    Admin :
        - peut consulter tous les abonnements

    Agronome :
        - peut consulter uniquement ses propres abonnements

    La création/modification/suppression sera gérée
    par des actions métier spécifiques.
    """

    serializer_class = AbonnementAgronomeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return AbonnementAgronome.objects.select_related(
                "agronome"
            ).all().order_by("-date_creation")

        return AbonnementAgronome.objects.select_related(
            "agronome"
        ).filter(
            agronome=user
        ).order_by("-date_creation")

    def create(self, request, *args, **kwargs):
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied(
            "La création d'un abonnement doit passer par le processus "
            "de souscription MBAAY."
        )

    def update(self, request, *args, **kwargs):
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied(
            "La modification d'un abonnement n'est pas autorisée directement."
        )

    def partial_update(self, request, *args, **kwargs):
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied(
            "La modification d'un abonnement n'est pas autorisée directement."
        )

    def destroy(self, request, *args, **kwargs):
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied(
            "La suppression d'un abonnement n'est pas autorisée."
        )