from rest_framework import serializers

from .models import (
    ModeLivraison,
    ParametreLivraison,
    ConfigurationLivraisonBoutique,
    ContactLivreur,
)


class ModeLivraisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeLivraison
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


class ParametreLivraisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParametreLivraison
        fields = [
            "id",
            "regroupement_automatique",
            "active",
            "date_modification",
        ]
        read_only_fields = [
            "id",
            "date_modification",
        ]


class ConfigurationLivraisonBoutiqueSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ConfigurationLivraisonBoutique

        fields = [
            "id",
            "boutique",
            "livraison_par_acheteur",
            "livraison_par_agronome",
            "nombre_max_commandes_par_livreur",
            "regroupement_automatique",
            "date_modification",
        ]

        read_only_fields = [
            "id",
            "boutique",
            "date_modification",
        ]
class ContactLivreurSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ContactLivreur

        fields = [
            "id",
            "boutique",
            "nom",
            "telephone",
            "actif",
            "date_creation",
        ]

        read_only_fields = [
            "id",
            "boutique",
            "date_creation",
        ]