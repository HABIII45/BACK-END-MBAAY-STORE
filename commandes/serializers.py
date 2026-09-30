from rest_framework import serializers

from .models import Commande, LigneCommande


class LigneCommandeSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(
        source="produit.nom",
        read_only=True
    )

    produit_image = serializers.ImageField(
        source="produit.image",
        read_only=True
    )

    unite_vente_symbole = serializers.CharField(
        source="produit.unite_vente.symbole",
        read_only=True
    )

    total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = LigneCommande

        fields = [
            "id",
            "produit",
            "produit_nom",
            "produit_image",
            "quantite",
            "prix_unitaire",
            "unite_vente_symbole",
            "total",
        ]

        read_only_fields = [
            "id",
            "produit_nom",
            "produit_image",
            "prix_unitaire",
            "unite_vente_symbole",
            "total",
        ]


class CommandeSerializer(serializers.ModelSerializer):

    boutique_nom = serializers.CharField(
        source="boutique.nom",
        read_only=True
    )

    boutique_slug = serializers.CharField(
        source="boutique.slug",
        read_only=True
    )

    mode_livraison_nom = serializers.CharField(
        source="mode_livraison.nom",
        read_only=True
    )

    lignes = LigneCommandeSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Commande

        fields = [
            "id",
            "reference",
            "boutique",
            "boutique_nom",
            "boutique_slug",
            "mode_livraison",
            "mode_livraison_nom",
            "statut",
            "sous_total",
            "frais_livraison",
            "total",
            "token_suivi",
            "code_reception",
            "lignes",
            "date_creation",
            "date_paiement",
            "date_livraison",
            "date_modification",
        ]

        read_only_fields = [
            "id",
            "reference",
            "boutique_nom",
            "boutique_slug",
            "mode_livraison_nom",
            "statut",
            "sous_total",
            "frais_livraison",
            "total",
            "token_suivi",
            "code_reception",
            "lignes",
            "date_creation",
            "date_paiement",
            "date_livraison",
            "date_modification",
        ]
        
        
        
class CommandeSuiviSerializer(serializers.ModelSerializer):
    boutique_nom = serializers.CharField(
        source="boutique.nom",
        read_only=True
    )

    boutique_slug = serializers.CharField(
        source="boutique.slug",
        read_only=True
    )

    mode_livraison_nom = serializers.CharField(
        source="mode_livraison.nom",
        read_only=True
    )

    lignes = LigneCommandeSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Commande

        fields = [
            "reference",
            "boutique_nom",
            "boutique_slug",
            "mode_livraison_nom",
            "statut",
            "sous_total",
            "frais_livraison",
            "total",
            "lignes",
            "date_creation",
            "date_paiement",
            "date_livraison",
            "date_modification",
        ]
        
        
        
        
        
class CommandeAgronomeSerializer(serializers.ModelSerializer):
    boutique_nom = serializers.CharField(
        source="boutique.nom",
        read_only=True
    )

    mode_livraison_nom = serializers.CharField(
        source="mode_livraison.nom",
        read_only=True
    )

    lignes = LigneCommandeSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Commande

        fields = [
            "id",
            "reference",
            "boutique",
            "boutique_nom",
            "mode_livraison_nom",
            "statut",
            "sous_total",
            "frais_livraison",
            "total",
            "token_suivi",
            "lignes",
            "date_creation",
            "date_paiement",
            "date_livraison",
            "date_modification",
        ]

        read_only_fields = fields