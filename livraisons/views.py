from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import (
    ModeLivraison,
    ParametreLivraison,
    ConfigurationLivraisonBoutique,
    ContactLivreur,
    TarifLivraisonDistance,
)

from .serializers import (
    ModeLivraisonSerializer,
    ParametreLivraisonSerializer,
    ConfigurationLivraisonBoutiqueSerializer,
    ContactLivreurSerializer,
    TarifLivraisonDistanceSerializer
)


from .permissions import (
    IsAdminMBAAY,
    IsAgronomeMBAAY,
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from boutiques.models import Boutique
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
    permission_classes = [IsAuthenticated,IsAgronomeMBAAY,]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return ConfigurationLivraisonBoutique.objects.none()

        return ConfigurationLivraisonBoutique.objects.filter(
            boutique__proprietaire=user
        )

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != "AGRONOME":
            raise PermissionDenied(
                "Seul un agronome peut configurer la livraison de sa boutique."
            )

        boutique = user.boutique

        if ConfigurationLivraisonBoutique.objects.filter(
            boutique=boutique
        ).exists():
            raise PermissionDenied(
                "La configuration de livraison de cette boutique existe déjà."
            )

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
        
class TarifLivraisonDistanceViewSet(viewsets.ModelViewSet):
    serializer_class = TarifLivraisonDistanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role != "AGRONOME":
            return TarifLivraisonDistance.objects.none()

        return TarifLivraisonDistance.objects.filter(
            configuration__boutique__proprietaire=user
        )

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != "AGRONOME":
            raise PermissionDenied(
                "Seul un agronome peut gérer ses tarifs de livraison."
            )

        try:
            configuration = user.boutique.configuration_livraison
        except ConfigurationLivraisonBoutique.DoesNotExist:
            raise PermissionDenied(
                "Vous devez d'abord créer votre configuration de livraison."
            )

        serializer.save(
            configuration=configuration
        )
        
        
        
        
class LivraisonBoutiquePubliqueView(APIView):
    """
    Informations de livraison accessibles à l'acheteur
    pour une boutique publiée.
    """

    permission_classes = [AllowAny]

    def get(self, request, boutique_id):

        boutique = get_object_or_404(
            Boutique,
            id=boutique_id,
            statut="PUBLIEE"
        )

        try:
            configuration = (
                ConfigurationLivraisonBoutique.objects
                .prefetch_related("modes_livraison")
                .get(boutique=boutique)
            )
        except ConfigurationLivraisonBoutique.DoesNotExist:
            return Response(
                {
                    "message": (
                        "Cette boutique ne possède pas encore "
                        "de configuration de livraison."
                    )
                },
                status=404
            )

        modes = configuration.modes_livraison.filter(
            active=True
        )

        return Response(
            {
                "boutique": boutique.id,
                "type_tarification": configuration.type_tarification,
                "frais_livraison_fixe": configuration.frais_livraison_fixe,
                "modes_livraison": [
                    {
                        "id": mode.id,
                        "nom": mode.nom,
                        "code": mode.code,
                        "description": mode.description,
                    }
                    for mode in modes
                ],
            }
        )