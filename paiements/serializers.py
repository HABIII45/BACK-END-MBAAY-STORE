from rest_framework import serializers


class PaiementAbonnementSerializer(serializers.Serializer):
    type_abonnement = serializers.ChoiceField(
        choices=["MENSUEL", "ANNUEL"],
        error_messages={
            "invalid_choice": "Le type d'abonnement doit être MENSUEL ou ANNUEL.",
            "required": "Le type d'abonnement est obligatoire.",
        },
    )
class EssaiGratuitSerializer(serializers.Serializer):
    confirmation = serializers.BooleanField(
        required=True
    )
    
from rest_framework import serializers
from utilisateurs.models import CompteReversement


class CompteReversementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteReversement

        fields = [
            "id",
            "account_alias",
            "actif",
            "date_creation",
            "date_modification",
        ]

        read_only_fields = [
            "id",
            "actif",
            "date_creation",
            "date_modification",
        ]