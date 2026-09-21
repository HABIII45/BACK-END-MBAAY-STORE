from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import (
    ModeLivraison,
    ParametreLivraison,
    ConfigurationLivraisonBoutique,
    ContactLivreur,
)

from .serializers import (
    ModeLivraisonSerializer,
    ParametreLivraisonSerializer,
    ConfigurationLivraisonBoutiqueSerializer,
    ContactLivreurSerializer,
)

from .permissions import (
    IsAdminMBAAY,
)


# ============================================================
# MODES DE LIVRAISON
# ============================================================

class ModeLivraisonViewSet(viewsets.ModelViewSet):
    queryset = ModeLivraison.objects.all()
    serializer_class = ModeLivraisonSerializer

    def get_permissions(self):
        """
        Les modes de livraison sont une configuration MBAAY.

        ADMIN :
            peut créer, modifier, activer, désactiver et supprimer.

        AGRONOME :
            peut uniquement consulter les modes disponibles.
        """

        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            permission_classes = [IsAdminMBAAY]

        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        L'agronome ne voit que les modes actifs.

        L'admin voit tous les modes, y compris ceux désactivés.
        """

        user = self.request.user

        if user.role == "ADMIN":
            return ModeLivraison.objects.all()

        return ModeLivraison.objects.filter(
            active=True
        )


# ============================================================
# PARAMÈTRES GLOBAUX DE LIVRAISON
# ============================================================

class ParametreLivraisonViewSet(viewsets.ModelViewSet):
    queryset = ParametreLivraison.objects.all()
    serializer_class = ParametreLivraisonSerializer

    def get_permissions(self):
        """
        Les paramètres globaux appartiennent à MBAAY.

        ADMIN :
            CRUD complet.

        AGRONOME :
            lecture uniquement.
        """

        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            permission_classes = [IsAdminMBAAY]

        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]


# ============================================================
# CONFIGURATION DE LIVRAISON D'UNE BOUTIQUE
# ============================================================

class ConfigurationLivraisonBoutiqueViewSet(viewsets.ModelViewSet):
    serializer_class = ConfigurationLivraisonBoutiqueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Chaque agronome ne voit que la configuration
        de sa propre boutique.
        """

        user = self.request.user

        if user.role == "ADMIN":
            return ConfigurationLivraisonBoutique.objects.none()

        return ConfigurationLivraisonBoutique.objects.filter(
            boutique__proprietaire=user
        )

    def perform_create(self, serializer):
        """
        La boutique est automatiquement déterminée
        à partir de l'utilisateur connecté.
        """

        user = self.request.user

        if user.role != "AGRONOME":
            raise PermissionDenied(
              "Seul un agronome peut configurer la livraison de sa boutique."
            )

        boutique = user.boutique

        serializer.save(
            boutique=boutique
        )


# ============================================================
# CONTACTS DES LIVREURS
# ============================================================

class ContactLivreurViewSet(viewsets.ModelViewSet):
    serializer_class = ContactLivreurSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Un agronome ne voit que les livreurs
        appartenant à sa boutique.
        """

        user = self.request.user

        if user.role == "ADMIN":
            return ContactLivreur.objects.none()

        return ContactLivreur.objects.filter(
            boutique__proprietaire=user
        )

    def perform_create(self, serializer):
        """
        Le livreur est automatiquement rattaché
        à la boutique de l'agronome connecté.
        """

        user = self.request.user

        if user.role != "AGRONOME":
            raise PermissionDenied(
              "Seul un agronome peut ajouter un livreur."
         )

        boutique = user.boutique

        serializer.save(
            boutique=boutique
        )