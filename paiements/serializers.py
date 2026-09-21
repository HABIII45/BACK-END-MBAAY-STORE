from rest_framework import serializers


class PaiementAbonnementSerializer(serializers.Serializer):
    type_abonnement = serializers.ChoiceField(
        choices=["MENSUEL", "ANNUEL"],
        error_messages={
            "invalid_choice": "Le type d'abonnement doit être MENSUEL ou ANNUEL.",
            "required": "Le type d'abonnement est obligatoire.",
        },
    )