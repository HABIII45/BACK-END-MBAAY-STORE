from decimal import Decimal
import hashlib
import hmac
import json

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from abonnements.models import Abonnement, AbonnementAgronome

from .models import Paiement
from .serializers import PaiementAbonnementSerializer
from .services.paydunya import creer_facture_abonnement


class CreerPaiementAbonnementView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        utilisateur = request.user

        # -------------------------------------------------
        # 1. Vérifier le rôle
        # -------------------------------------------------

        if utilisateur.role != "AGRONOME":
            return Response(
                {
                    "detail": "Seul un agronome peut souscrire à un abonnement."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # -------------------------------------------------
        # 2. Valider la demande
        # -------------------------------------------------

        serializer = PaiementAbonnementSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        type_abonnement = serializer.validated_data[
            "type_abonnement"
        ]

        # -------------------------------------------------
        # 3. Récupérer la configuration active
        # -------------------------------------------------

        configuration = (
            Abonnement.objects
            .filter(actif=True)
            .order_by("-date_modification")
            .first()
        )

        if not configuration:
            return Response(
                {
                    "detail": "Aucune configuration d'abonnement active."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # 4. Déterminer le prix côté serveur
        # -------------------------------------------------

        if type_abonnement == "MENSUEL":
            montant = configuration.prix_mensuel
        else:
            montant = configuration.prix_annuel

        if montant <= Decimal("0"):
            return Response(
                {
                    "detail": "Le prix de cet abonnement n'est pas configuré."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # 5. Dates de l'abonnement
        # -------------------------------------------------

        maintenant = timezone.now()

        if type_abonnement == "MENSUEL":
            date_fin = maintenant + timezone.timedelta(
                days=30
            )
        else:
            date_fin = maintenant + timezone.timedelta(
                days=365
            )

        # -------------------------------------------------
        # 6. Créer l'abonnement en attente
        # -------------------------------------------------

        abonnement = AbonnementAgronome.objects.create(
            agronome=utilisateur,
            type_abonnement=type_abonnement,
            date_debut=maintenant,
            date_fin=date_fin,
            statut="SUSPENDU",
            statut_paiement="EN_ATTENTE",
        )

        # -------------------------------------------------
        # 7. Générer une référence MBAAY
        # -------------------------------------------------

        reference = (
            f"MBAAY-ABN-{utilisateur.id}-"
            f"{abonnement.id}-"
            f"{int(maintenant.timestamp())}"
        )

        # -------------------------------------------------
        # 8. Créer le paiement
        # -------------------------------------------------

        paiement = Paiement.objects.create(
            utilisateur=utilisateur,
            abonnement=abonnement,
            type_paiement="ABONNEMENT",
            montant=montant,
            statut="EN_ATTENTE",
            reference=reference,
        )

        # -------------------------------------------------
        # 9. Créer la facture PayDunya
        # -------------------------------------------------

        resultat = creer_facture_abonnement(
            paiement=paiement,
            nom_client=(
                f"{utilisateur.prenom} "
                f"{utilisateur.nom}"
            ),
            email_client=utilisateur.email,
        )

        # -------------------------------------------------
        # 10. Échec de création PayDunya
        # -------------------------------------------------

        if not resultat["success"]:

            abonnement.statut = "SUSPENDU"
            abonnement.statut_paiement = "ECHEC"

            abonnement.save(
                update_fields=[
                    "statut",
                    "statut_paiement",
                    "date_modification",
                ]
            )

            paiement.statut = "ECHEC"

            paiement.save(
                update_fields=[
                    "statut",
                    "date_modification",
                ]
            )

            return Response(
                {
                    "detail": resultat["message"]
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # -------------------------------------------------
        # 11. Réponse au frontend
        # -------------------------------------------------

        return Response(
            {
                "message": "Facture PayDunya créée.",
                "reference": paiement.reference,
                "paiement_id": paiement.id,
                "abonnement_id": abonnement.id,
                "montant": str(paiement.montant),
                "type_abonnement": abonnement.type_abonnement,
                "url_paiement": resultat["url_paiement"],
            },
            status=status.HTTP_201_CREATED,
        )


class PaydunyaIPNView(APIView):
    """
    Reçoit les notifications de paiement envoyées
    par PayDunya.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):

        try:

            # -------------------------------------------------
            # 1. Récupérer les données PayDunya
            # -------------------------------------------------

            data = request.data.get("data")

            if isinstance(data, str):
                data = json.loads(data)

            if not isinstance(data, dict):
                return Response(
                    {
                        "detail": "Données IPN invalides."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # -------------------------------------------------
            # 2. Récupérer le hash
            # -------------------------------------------------

            hash_recu = data.get("hash")

            if not hash_recu:
                return Response(
                    {
                        "detail": "Hash PayDunya manquant."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # -------------------------------------------------
            # 3. Calculer le hash attendu
            # -------------------------------------------------

            hash_attendu = hashlib.sha512(
                settings.PAYDUNYA_MASTER_KEY.encode("utf-8")
            ).hexdigest()

            # -------------------------------------------------
            # 4. Vérifier la signature
            # -------------------------------------------------

            if not hmac.compare_digest(
                hash_recu,
                hash_attendu
            ):
                return Response(
                    {
                        "detail": "Signature PayDunya invalide."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # -------------------------------------------------
            # 5. Récupérer le statut
            # -------------------------------------------------

            statut_paydunya = data.get("status")

            # -------------------------------------------------
            # 6. Récupérer la facture
            # -------------------------------------------------

            invoice = data.get("invoice") or {}

            token_paydunya = invoice.get("token")
            montant_paydunya = invoice.get("total_amount")

            if not token_paydunya:
                return Response(
                    {
                        "detail": "Token PayDunya manquant."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # -------------------------------------------------
            # 7. Rechercher le paiement MBAAY
            # -------------------------------------------------

            paiement = (
                Paiement.objects
                .select_related("abonnement")
                .filter(
                    token_paydunya=token_paydunya
                )
                .first()
            )

            if not paiement:
                return Response(
                    {
                        "detail": "Paiement MBAAY introuvable."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # -------------------------------------------------
            # 8. Vérifier le montant
            # -------------------------------------------------

            if montant_paydunya is not None:

                montant_attendu = Decimal(
                    str(paiement.montant)
                )

                montant_recu = Decimal(
                    str(montant_paydunya)
                )

                if montant_recu != montant_attendu:

                    paiement.statut = "ECHEC"

                    paiement.save(
                        update_fields=[
                            "statut",
                            "date_modification",
                        ]
                    )

                    return Response(
                        {
                            "detail": (
                                "Le montant du paiement "
                                "ne correspond pas."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # -------------------------------------------------
            # 9. Paiement confirmé
            # -------------------------------------------------

            if statut_paydunya == "completed":

                # Évite de traiter deux fois
                # la même notification.

                if paiement.statut != "PAYE":

                    paiement.statut = "PAYE"
                    paiement.date_paiement = timezone.now()

                    paiement.save(
                        update_fields=[
                            "statut",
                            "date_paiement",
                            "date_modification",
                        ]
                    )

                    abonnement = paiement.abonnement

                    if abonnement:

                        abonnement.statut = "ACTIF"
                        abonnement.statut_paiement = "PAYE"

                        abonnement.save(
                            update_fields=[
                                "statut",
                                "statut_paiement",
                                "date_modification",
                            ]
                        )

                return Response(
                    {
                        "message": (
                            "Paiement confirmé avec succès."
                        )
                    },
                    status=status.HTTP_200_OK,
                )

            # -------------------------------------------------
            # 10. Paiement échoué
            # -------------------------------------------------

            if statut_paydunya == "failed":

                paiement.statut = "ECHEC"

                paiement.save(
                    update_fields=[
                        "statut",
                        "date_modification",
                    ]
                )

                if paiement.abonnement:

                    paiement.abonnement.statut_paiement = "ECHEC"

                    paiement.abonnement.save(
                        update_fields=[
                            "statut_paiement",
                            "date_modification",
                        ]
                    )

                return Response(
                    {
                        "message": "Paiement échoué."
                    },
                    status=status.HTTP_200_OK,
                )

            # -------------------------------------------------
            # 11. Paiement annulé
            # -------------------------------------------------

            if statut_paydunya == "canceled":

                paiement.statut = "ANNULE"

                paiement.save(
                    update_fields=[
                        "statut",
                        "date_modification",
                    ]
                )

                return Response(
                    {
                        "message": "Paiement annulé."
                    },
                    status=status.HTTP_200_OK,
                )

            # -------------------------------------------------
            # 12. Statut non traité
            # -------------------------------------------------

            return Response(
                {
                    "message": (
                        "Notification PayDunya reçue."
                    ),
                    "status": statut_paydunya,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:

            return Response(
                {
                    "detail": (
                        "Erreur lors du traitement "
                        "de l'IPN."
                    ),
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )