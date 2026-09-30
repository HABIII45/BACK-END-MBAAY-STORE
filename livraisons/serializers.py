from rest_framework import serializers

from .models import (
    ModeLivraison,
    ParametreLivraison,
    ConfigurationLivraisonBoutique,
    ContactLivreur,
    TarifLivraisonDistance,
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
            "modes_livraison",
            "type_tarification",
            "frais_livraison_fixe",
            "nombre_max_commandes_par_livreur",
            "regroupement_automatique",
            "date_modification",
        ]

        read_only_fields = [
            "id",
            "boutique",
            "date_modification",
        ]

    def validate_modes_livraison(self, modes):
        """
        Vérifie que l'agronome ne sélectionne
        que des modes activés par MBAAY.
        """
        modes_inactifs = modes.filter(active=False)

        if modes_inactifs.exists():
            raise serializers.ValidationError(
                "Vous ne pouvez pas sélectionner un mode de livraison désactivé par MBAAY."
            )

        return modes


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


class TarifLivraisonDistanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = TarifLivraisonDistance

        fields = [
            "id",
            "configuration",
            "distance_min_km",
            "distance_max_km",
            "montant",
        ]

        read_only_fields = [
            "id",
            "configuration",
        ]