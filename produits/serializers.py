from rest_framework import serializers

from .models import (
   
    Produit,
)



class ProduitSerializer(serializers.ModelSerializer):

    categorie_nom = serializers.CharField(
        source="categorie.nom",
        read_only=True
    )

    unite_vente_nom = serializers.CharField(
        source="unite_vente.nom",
        read_only=True
    )

    unite_vente_symbole = serializers.CharField(
        source="unite_vente.symbole",
        read_only=True
    )

    class Meta:
        model = Produit

        fields = [
            "id",
            "boutique",
            "nom",
            "description",
            "prix",
            "categorie",
            "categorie_nom",
            "unite_vente",
            "unite_vente_nom",
            "unite_vente_symbole",
            "stock_initial",
            "stock_actuel",
            "quantite_vendue",
            "disponible",
            "image",
            "date_creation",
            "date_modification",
        ]

        read_only_fields = [
            "id",
            "boutique",
            "stock_actuel",
            "quantite_vendue",
            "date_creation",
            "date_modification",
            "categorie_nom",
            "unite_vente_nom",
            "unite_vente_symbole",
        ]

    def create(self, validated_data):
        """
        Lors de la création :
        stock_initial = quantité déclarée par l'agronome
        stock_actuel = stock_initial
        """

        validated_data["stock_actuel"] = validated_data["stock_initial"]

        return super().create(validated_data)
    
class ProduitPublicSerializer(serializers.ModelSerializer):
    
    categorie_nom = serializers.CharField(
        source="categorie.nom",
        read_only=True
    )

    unite_vente_nom = serializers.CharField(
        source="unite_vente.nom",
        read_only=True
    )

    unite_vente_symbole = serializers.CharField(
        source="unite_vente.symbole",
        read_only=True
    )

    boutique_nom = serializers.CharField(
        source="boutique.nom",
        read_only=True
    )

    boutique_slug = serializers.CharField(
        source="boutique.slug",
        read_only=True
    )

    class Meta:
        model = Produit

        fields = [
            "id",
            "nom",
            "description",
            "prix",
            "image",
            "categorie",
            "categorie_nom",
            "unite_vente",
            "unite_vente_nom",
            "unite_vente_symbole",
            "stock_actuel",
            "disponible",
            "boutique",
            "boutique_nom",
            "boutique_slug",
        ]

        read_only_fields = fields