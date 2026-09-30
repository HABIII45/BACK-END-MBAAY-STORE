from rest_framework import serializers

from .models import InformationAgricole


class InformationAgricoleSerializer(serializers.ModelSerializer):

    categorie_display = serializers.CharField(
        source="get_categorie_display",
        read_only=True
    )

    class Meta:
        model = InformationAgricole
        fields = [
            "id",
            "titre",
            "description",
            "categorie",
            "categorie_display",
            "source",
            "url",
            "date_publication",
            "date_evenement",
        ]