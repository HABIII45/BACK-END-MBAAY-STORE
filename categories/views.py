from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Categorie, UniteVente, MoyenPaiement
from .serializers import (
    CategorieSerializer,
    UniteVenteSerializer,
    MoyenPaiementSerializer,
)


class CategorieViewSet(viewsets.ModelViewSet):
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer
    permission_classes = [IsAuthenticated]


class UniteVenteViewSet(viewsets.ModelViewSet):
    queryset = UniteVente.objects.all()
    serializer_class = UniteVenteSerializer
    permission_classes = [IsAuthenticated]


class MoyenPaiementViewSet(viewsets.ModelViewSet):
    queryset = MoyenPaiement.objects.all()
    serializer_class = MoyenPaiementSerializer
    permission_classes = [IsAuthenticated]