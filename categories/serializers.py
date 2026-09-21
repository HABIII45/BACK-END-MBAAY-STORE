from rest_framework import serializers
from .models import Categorie
from .models import UniteVente,MoyenPaiement


class CategorieSerializer(serializers.ModelSerializer):

    class Meta:
        model = Categorie
        fields = [
            "id",
            "nom",
            "description",
            "active",
            "date_creation",
        ]
        read_only_fields = [
            "id",
            "date_creation",
        ]
class UniteVenteSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = UniteVente
        fields = [
            "id",
            "nom",
            "symbole",
            "description",
            "active",
            "date_creation",
        ]
        read_only_fields = [
            "id",
            "date_creation",
        ]
class MoyenPaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoyenPaiement
        fields = [
            "id",
            "nom",
            "code",
            "description",
            "active",
            "date_creation",
        ]
        read_only_fields = [
            "id",
            "date_creation",
        ]