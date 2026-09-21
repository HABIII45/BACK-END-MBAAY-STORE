from rest_framework import serializers

from .models import Abonnement, AbonnementAgronome


class AbonnementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abonnement

        fields = [
            "id",
            "prix_mensuel",
            "prix_annuel",
            "essai_gratuit_actif",
            "duree_essai_jours",
            "actif",
            "date_creation",
            "date_modification",
        ]

        read_only_fields = [
            "id",
            "date_creation",
            "date_modification",
        ]

    def validate(self, attrs):
        prix_mensuel = attrs.get(
            "prix_mensuel",
            getattr(self.instance, "prix_mensuel", None)
        )

        prix_annuel = attrs.get(
            "prix_annuel",
            getattr(self.instance, "prix_annuel", None)
        )

        essai_actif = attrs.get(
            "essai_gratuit_actif",
            getattr(self.instance, "essai_gratuit_actif", True)
        )

        duree_essai = attrs.get(
            "duree_essai_jours",
            getattr(self.instance, "duree_essai_jours", 30)
        )

        # Vérification du prix mensuel
        if prix_mensuel is not None and prix_mensuel < 0:
            raise serializers.ValidationError({
                "prix_mensuel": (
                    "Le prix mensuel ne peut pas être négatif."
                )
            })

        # Vérification du prix annuel
        if prix_annuel is not None and prix_annuel < 0:
            raise serializers.ValidationError({
                "prix_annuel": (
                    "Le prix annuel ne peut pas être négatif."
                )
            })

        # Vérification de la durée de l'essai
        if essai_actif and duree_essai <= 0:
            raise serializers.ValidationError({
                "duree_essai_jours": (
                    "La durée de l'essai doit être supérieure à 0 jour."
                )
            })

        return attrs


class AbonnementAgronomeSerializer(serializers.ModelSerializer):

    agronome_nom = serializers.SerializerMethodField()

    def get_agronome_nom(self, obj):
        return f"{obj.agronome.prenom} {obj.agronome.nom}"

    class Meta:
        model = AbonnementAgronome

        fields = [
            "id",
            "agronome",
            "agronome_nom",
            "type_abonnement",
            "date_debut",
            "date_fin",
            "statut",
            "statut_paiement",
            "date_creation",
            "date_modification",
        ]

        read_only_fields = [
            "id",
            "agronome",
            "agronome_nom",
            "date_creation",
            "date_modification",
        ]