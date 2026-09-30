from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import (
   
    Produit,
)

from .serializers import (
   
    ProduitSerializer,
     ProduitPublicSerializer,
)
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from utilisateurs.permissions import IsAgronomeMBAAY 
from django.core.exceptions import ObjectDoesNotExist



class ProduitViewSet(viewsets.ModelViewSet):
    serializer_class = ProduitSerializer
    #permission_classes = [IsAuthenticated]
    permission_classes = [
    IsAuthenticated,
    IsAgronomeMBAAY,
]

    def get_queryset(self):
     try:
        boutique = self.request.user.boutique
     except ObjectDoesNotExist:
        return Produit.objects.none()

     return Produit.objects.filter(
        boutique=boutique
    )

    def perform_create(self, serializer):
        """
        La boutique est automatiquement récupérée
        depuis le compte de l'agronome connecté.
        """

        boutique = self.request.user.boutique

        serializer.save(
            boutique=boutique
        )
        
class ProduitPublicListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        produits = (
            Produit.objects
            .filter(
                disponible=True,
                stock_actuel__gt=0,
                boutique__statut="PUBLIEE",
            )
            .select_related(
                "boutique",
                "categorie",
                "unite_vente",
            )
        )

        serializer = ProduitPublicSerializer(
            produits,
            many=True,
            context={"request": request},
        )

        return Response({
            "success": True,
            "nombre": produits.count(),
            "produits": serializer.data,
        })