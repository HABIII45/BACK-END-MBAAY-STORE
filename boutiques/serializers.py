from rest_framework import serializers
from .models import Boutique


class BoutiqueSerializer(serializers.ModelSerializer):

    class Meta:
        model = Boutique
        fields = [
            "id",
            "nom",
            "slug",
            "description",
            "logo",
            "image",
            "couleur_principale",
            "statut",
            "date_creation",
            "date_modification",
            "latitude",
            "longitude",
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