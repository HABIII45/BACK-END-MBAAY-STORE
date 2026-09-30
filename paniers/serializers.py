
from rest_framework import serializers

from .models import Panier, LignePanier


class LignePanierSerializer(serializers.ModelSerializer):

    produit_nom = serializers.CharField(
        source="produit.nom",
        read_only=True
    )

    produit_image = serializers.ImageField(
        source="produit.image",
        read_only=True
    )

    boutique_nom = serializers.CharField(
        source="produit.boutique.nom",
        read_only=True
    )

    boutique_slug = serializers.CharField(
        source="produit.boutique.slug",
        read_only=True
    )
    boutique = serializers.IntegerField(
    source="produit.boutique.id",
    read_only=True
)
    unite_vente_symbole = serializers.CharField(
        source="produit.unite_vente.symbole",
        read_only=True
    )

    total = serializers.SerializerMethodField()

    class Meta:
        model = LignePanier

        fields = [
            "id",
            "produit",
            "produit_nom",
            "produit_image",
             "boutique",
            "boutique_nom",
            "boutique_slug",
            "quantite",
            "prix_unitaire",
            "unite_vente_symbole",
            "total",
        ]

        read_only_fields = [
            "id",
            "produit_nom",
            "produit_image",
            "boutique",
            "boutique_nom",
            "boutique_slug",
            "prix_unitaire",
            "unite_vente_symbole",
            "total",
        ]

    def get_total(self, obj):
        return obj.quantite * obj.prix_unitaire


class PanierSerializer(serializers.ModelSerializer):

    lignes = LignePanierSerializer(
        many=True,
        read_only=True
    )

    total = serializers.SerializerMethodField()

    nombre_articles = serializers.SerializerMethodField()

    class Meta:
        model = Panier

        fields = [
            "identifiant",
            "date_creation",
            "date_modification",
            "lignes",
            "nombre_articles",
            "total",
        ]

        read_only_fields = [
            "identifiant",
            "date_creation",
            "date_modification",
            "lignes",
            "nombre_articles",
            "total",
        ]

    def get_total(self, obj):
        return sum(
            (
                ligne.quantite * ligne.prix_unitaire
                for ligne in obj.lignes.all()
            ),
            0
        )

    def get_nombre_articles(self, obj):
        return sum(
            ligne.quantite
            for ligne in obj.lignes.all()
        )

