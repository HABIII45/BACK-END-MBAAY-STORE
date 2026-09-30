from rest_framework import serializers

from .models import Boutique
from categories.models import MoyenPaiement


class BoutiqueSerializer(serializers.ModelSerializer):

    moyens_paiement = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=MoyenPaiement.objects.filter(active=True),
        required=False
    )

    class Meta:
        model = Boutique

        fields = [
            "id",
            "nom",
            "slug",
            "description",
            "logo",
            "image",
            "photo_agronome",
            "couleur_principale",
            "palette",
            "tiktok",
           "facebook",
            
            "statut",
            "date_creation",
            "date_modification",
            "latitude",
            "longitude",
            "moyens_paiement",
        ]

        read_only_fields = [
            "id",
            "slug",
            "statut",
            "date_creation",
            "date_modification",
        ]


class CreationEspaceSerializer(serializers.Serializer):

    # Informations du compte
    prenom = serializers.CharField(max_length=100)
    nom = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    telephone = serializers.CharField(max_length=20)

    # Informations de la boutique
    nom_boutique = serializers.CharField(max_length=150)
    description_boutique = serializers.CharField()

    # Localisation de la boutique
    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6
    )
    
    
#serializers boutique pour l'acheteur

from rest_framework import serializers

from .models import Boutique


class BoutiqueAcheteurSerializer(serializers.ModelSerializer):

    class Meta:
        model = Boutique

        fields = [
            "id",
            "nom",
            "slug",
            "description",
            "logo",
            "image",
        ]

# =========================================================
# SERIALIZERS RECHERCHE ACHETEUR
# =========================================================

from produits.models import Produit


class ProduitRechercheAcheteurSerializer(
    serializers.ModelSerializer
):

    unite = serializers.CharField(
        source="unite_vente.symbole"
    )

    class Meta:
        model = Produit

        fields = [
            "id",
            "nom",
            "description",
            "prix",
            "unite",
            "stock_actuel",
            "image",
        ]


class BoutiqueRechercheAcheteurSerializer(
    serializers.ModelSerializer
):

    produits = ProduitRechercheAcheteurSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Boutique

        fields = [
            "id",
            "nom",
            "slug",
            "description",
            "logo",
            "image",
            "produits",
        ]
        
        
# =========================================================
# SERIALIZER BOUTIQUE PUBLIQUE
# =========================================================

class ProduitBoutiquePubliqueSerializer(serializers.ModelSerializer):

    unite = serializers.CharField(
        source="unite_vente.symbole",
        read_only=True
    )

    class Meta:
        model = Produit

        fields = [
            "id",
            "nom",
            "description",
            "prix",
            "unite",
            "stock_actuel",
            "image",
        ]


class BoutiquePubliqueSerializer(serializers.ModelSerializer):
    
    produits = ProduitBoutiquePubliqueSerializer(
        many=True,
        read_only=True
    )

    moyens_paiement = serializers.SerializerMethodField()

    class Meta:
        model = Boutique

        fields = [
            "id",
            "nom",
            "slug",
            "description",
            "logo",
            "image",
            "photo_agronome",
            "couleur_principale",
            "palette",
            "tiktok",
            "facebook",
            "latitude",
            "longitude",
            "moyens_paiement",
            "produits",
        ]

    def get_moyens_paiement(self, obj):
        return [
            {
                "id": moyen.id,
                "nom": moyen.nom,
            }
            for moyen in obj.moyens_paiement.filter(active=True)
        ]