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
from .serializers import PaiementAbonnementSerializer,CompteReversementSerializer
from .services.paydunya import creer_facture_abonnement
import secrets
from rest_framework.permissions import AllowAny
from commandes.models import Commande
from .services import creer_facture_commande
from utilisateurs.models import CompteReversement


class CreerPaiementAbonnementView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        utilisateur = request.user

        # ------------------------------------------------------
        # 1. Vérifier que l'utilisateur est un agronome
        # ------------------------------------------------------

        if utilisateur.role != "AGRONOME":
            return Response(
                {
                    "success": False,
                    "message": "Seul un agronome peut souscrire à un abonnement."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ------------------------------------------------------
        # 2. Valider le type d'abonnement
        # ------------------------------------------------------

        serializer = PaiementAbonnementSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        type_abonnement = serializer.validated_data["type_abonnement"]

        # ------------------------------------------------------
        # 3. Récupérer la configuration active
        # ------------------------------------------------------

        configuration = (
            Abonnement.objects
            .filter(actif=True)
            .order_by("-date_modification")
            .first()
        )

        if not configuration:
            return Response(
                {
                    "success": False,
                    "message": "Aucune configuration d'abonnement active."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ------------------------------------------------------
        # 4. Vérifier qu'il n'existe pas déjà un abonnement actif
        # ------------------------------------------------------

        abonnement_actif = (
            AbonnementAgronome.objects
            .filter(
                agronome=utilisateur,
                statut="ACTIF",
            )
            .exists()
        )

        if abonnement_actif:
            return Response(
                {
                    "success": False,
                    "message": "Vous disposez déjà d'un abonnement actif."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ------------------------------------------------------
        # 5. Déterminer le prix et la durée
        # ------------------------------------------------------

        maintenant = timezone.now()

        if type_abonnement == "MENSUEL":
            montant = configuration.prix_mensuel
            date_fin = maintenant + timezone.timedelta(days=30)

        else:
            montant = configuration.prix_annuel
            date_fin = maintenant + timezone.timedelta(days=365)

        if montant <= Decimal("0.00"):
            return Response(
                {
                    "success": False,
                    "message": "Le prix de l'abonnement est invalide."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ------------------------------------------------------
        # 6. Créer l'abonnement en attente de paiement
        # ------------------------------------------------------

        abonnement = AbonnementAgronome.objects.create(
            agronome=utilisateur,
            type_abonnement=type_abonnement,
            date_debut=maintenant,
            date_fin=date_fin,
            statut="SUSPENDU",
            statut_paiement="EN_ATTENTE",
        )

        # ------------------------------------------------------
        # 7. Créer le paiement
        # ------------------------------------------------------

        reference = (
            f"MBAAY-ABO-"
            f"{secrets.token_hex(5).upper()}"
        )

        paiement = Paiement.objects.create(
            utilisateur=utilisateur,
            abonnement=abonnement,
            type_paiement="ABONNEMENT",
            montant=montant,
            statut="EN_ATTENTE",
            reference=reference,
        )

        # ------------------------------------------------------
        # 8. Créer la facture PayDunya
        # ------------------------------------------------------

        resultat = creer_facture_abonnement(
            paiement=paiement,
            abonnement=abonnement,
        )

        if not resultat.get("success"):
            paiement.statut = "ECHEC"
            paiement.save(
                update_fields=[
                    "statut",
                    "date_modification",
                ]
            )

            abonnement.statut_paiement = "ECHEC"
            abonnement.save(
                update_fields=[
                    "statut_paiement",
                    "date_modification",
                ]
            )

            return Response(
                {
                    "success": False,
                    "message": resultat.get(
                        "message",
                        "Impossible de créer la facture PayDunya."
                    ),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # ------------------------------------------------------
        # 9. Retourner le lien de paiement
        # ------------------------------------------------------

        return Response(
            {
                "success": True,
                "message": "Paiement de l'abonnement initialisé.",
                "paiement": {
                    "id": paiement.id,
                    "reference": paiement.reference,
                    "montant": str(paiement.montant),
                    "statut": paiement.statut,
                },
                "abonnement": {
                    "id": abonnement.id,
                    "type": abonnement.type_abonnement,
                },
                "checkout_url": resultat["url_paiement"],
            },
            status=status.HTTP_201_CREATED,
        )



class PaydunyaIPNView(APIView):
    authentication_classes = []
    permission_classes = []

    @transaction.atomic
    def post(self, request):
        try:
            # ==========================================================
            # 1. Récupération des données envoyées par PayDunya
            # ==========================================================

            data = request.data.get("data")

            if isinstance(data, str):
                data = json.loads(data)

            if not isinstance(data, dict):
                return Response(
                    {
                        "success": False,
                        "message": "Données IPN invalides."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ==========================================================
            # 2. Vérification du hash PayDunya
            # ==========================================================

            hash_recu = data.get("hash")

            if not hash_recu:
                return Response(
                    {
                        "success": False,
                        "message": "Hash manquant."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            hash_attendu = hashlib.sha512(
                settings.PAYDUNYA_MASTER_KEY.encode("utf-8")
            ).hexdigest()

            if not hmac.compare_digest(
                hash_recu,
                hash_attendu
            ):
                return Response(
                    {
                        "success": False,
                        "message": "Signature invalide."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # ==========================================================
            # 3. Récupération des informations du paiement
            # ==========================================================

            statut_paydunya = data.get("status")

            invoice = data.get("invoice") or {}

            token_paydunya = invoice.get("token")
            montant_paydunya = invoice.get("total_amount")

            if not token_paydunya:
                return Response(
                    {
                        "success": False,
                        "message": "Token PayDunya manquant."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ==========================================================
            # 4. Recherche du paiement + verrouillage
            # ==========================================================

            paiement = (
                Paiement.objects
                .select_for_update()
                .select_related("abonnement")
                .filter(
                    token_paydunya=token_paydunya
                )
                .first()
            )

            if not paiement:
                return Response(
                    {
                        "success": False,
                        "message": "Paiement introuvable."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # ==========================================================
            # 5. Vérification du montant
            # ==========================================================

            if montant_paydunya is not None:

                montant_attendu = Decimal(
                    str(paiement.montant)
                )

                montant_recu = Decimal(
                    str(montant_paydunya)
                )

                if montant_recu != montant_attendu:

                    # Ne jamais transformer un paiement déjà confirmé
                    # en échec à cause d'une notification ultérieure.
                    if paiement.statut != "PAYE":
                        paiement.statut = "ECHEC"

                        paiement.save(
                            update_fields=[
                                "statut",
                                "date_modification",
                            ]
                        )

                    return Response(
                        {
                            "success": False,
                            "message": (
                                "Le montant du paiement "
                                "ne correspond pas."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # ==========================================================
            # 6. PAIEMENT RÉUSSI
            # ==========================================================

            if statut_paydunya == "completed":

                # ------------------------------------------------------
                # Paiement déjà traité
                # ------------------------------------------------------

                if paiement.statut == "PAYE":
                    return Response(
                        {
                            "success": True,
                            "message": (
                                "Paiement déjà confirmé."
                            )
                        },
                        status=status.HTTP_200_OK
                    )

                # ------------------------------------------------------
                # Confirmation du paiement
                # ------------------------------------------------------

                paiement.statut = "PAYE"
                paiement.date_paiement = timezone.now()

                paiement.save(
                    update_fields=[
                        "statut",
                        "date_paiement",
                        "date_modification",
                    ]
                )

                # ======================================================
                # CAS 1 : ABONNEMENT
                # ======================================================

                if paiement.type_paiement == "ABONNEMENT":

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

                # ======================================================
                # CAS 2 : COMMANDE
                # ======================================================

                elif paiement.type_paiement == "COMMANDE":

                    commandes = (
                        paiement.commandes
                        .select_for_update()
                        .all()
                    )

                    maintenant = timezone.now()

                    for commande in commandes:

                        if commande.statut == "EN_ATTENTE_PAIEMENT":

                            commande.statut = "PAYEE"
                            commande.date_paiement = maintenant

                            commande.save(
                                update_fields=[
                                    "statut",
                                    "date_paiement",
                                    "date_modification",
                                ]
                            )

                return Response(
                    {
                        "success": True,
                        "message": (
                            "Paiement confirmé avec succès."
                        )
                    },
                    status=status.HTTP_200_OK
                )

            # ==========================================================
            # 7. PAIEMENT ÉCHOUÉ
            # ==========================================================

            if statut_paydunya == "failed":

                # Ne pas écraser un paiement déjà confirmé
                if paiement.statut != "PAYE":

                    paiement.statut = "ECHEC"

                    paiement.save(
                        update_fields=[
                            "statut",
                            "date_modification",
                        ]
                    )

                    if paiement.type_paiement == "ABONNEMENT":

                        abonnement = paiement.abonnement

                        if abonnement:
                            abonnement.statut_paiement = "ECHEC"

                            abonnement.save(
                                update_fields=[
                                    "statut_paiement",
                                    "date_modification",
                                ]
                            )

                return Response(
                    {
                        "success": True,
                        "message": "Paiement échoué enregistré."
                    },
                    status=status.HTTP_200_OK
                )

            # ==========================================================
            # 8. PAIEMENT ANNULÉ
            # ==========================================================

            if statut_paydunya == "canceled":

                # Ne pas écraser un paiement déjà confirmé
                if paiement.statut != "PAYE":

                    paiement.statut = "ANNULE"

                    paiement.save(
                        update_fields=[
                            "statut",
                            "date_modification",
                        ]
                    )

                return Response(
                    {
                        "success": True,
                        "message": "Paiement annulé enregistré."
                    },
                    status=status.HTTP_200_OK
                )

            # ==========================================================
            # 9. Autre statut PayDunya
            # ==========================================================

            return Response(
                {
                    "success": True,
                    "message": "Notification PayDunya reçue."
                },
                status=status.HTTP_200_OK
            )

        except (ValueError, TypeError, json.JSONDecodeError):
            return Response(
                {
                    "success": False,
                    "message": "Format des données IPN invalide."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "Erreur lors du traitement du paiement."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class ActiverEssaiGratuitView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        utilisateur = request.user

        if utilisateur.role != "AGRONOME":
            return Response(
                {
                    "detail": "Seul un agronome peut activer un essai gratuit."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

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

        if not configuration.essai_gratuit_actif:
            return Response(
                {
                    "detail": "L'essai gratuit n'est actuellement pas disponible."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        maintenant = timezone.now()

        abonnement_existant = (
            AbonnementAgronome.objects
            .filter(
                agronome=utilisateur,
                statut="ACTIF",
            )
            .exists()
        )

        if abonnement_existant:
            return Response(
                {
                    "detail": "Vous disposez déjà d'un abonnement actif."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        date_fin = (
            maintenant
            + timezone.timedelta(
                days=configuration.duree_essai_jours
            )
        )

        abonnement = AbonnementAgronome.objects.create(
            agronome=utilisateur,
            type_abonnement="ESSAI",
            date_debut=maintenant,
            date_fin=date_fin,
            statut="ACTIF",
            statut_paiement="NON_REQUIS",
        )

        return Response(
            {
                "message": "Essai gratuit activé avec succès.",
                "abonnement_id": abonnement.id,
                "type_abonnement": abonnement.type_abonnement,
                "date_debut": abonnement.date_debut,
                "date_fin": abonnement.date_fin,
                "statut": abonnement.statut,
            },
            status=status.HTTP_201_CREATED,
        )
        






class CreerPaiementCommandeView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        commande_ids = request.data.get("commandes", [])

        if not isinstance(commande_ids, list) or not commande_ids:
            return Response(
                {
                    "success": False,
                    "message": "Aucune commande fournie."
                },
                status=400
            )

        commandes = list(
            Commande.objects
            .select_for_update()
            .select_related(
                "boutique",
                "mode_livraison",
            )
            .prefetch_related(
                "lignes__produit"
            )
            .filter(
                id__in=commande_ids,
                statut="EN_ATTENTE_PAIEMENT"
            )
        )

        if not commandes:
            return Response(
                {
                    "success": False,
                    "message": "Aucune commande valide trouvée."
                },
                status=404
            )

        # Vérifier que toutes les commandes demandées existent
        ids_trouves = {commande.id for commande in commandes}
        ids_demandes = set(commande_ids)

        if ids_trouves != ids_demandes:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Une ou plusieurs commandes sont invalides "
                        "ou ne sont plus en attente de paiement."
                    )
                },
                status=400
            )

        montant_total = sum(
            (commande.total for commande in commandes),
            Decimal("0.00")
        )

        if montant_total <= 0:
            return Response(
                {
                    "success": False,
                    "message": "Le montant du paiement est invalide."
                },
                status=400
            )

        reference = (
            f"MBAAY-PAY-"
            f"{secrets.token_hex(5).upper()}"
        )

        paiement = Paiement.objects.create(
            utilisateur=None,
            type_paiement="COMMANDE",
            montant=montant_total,
            statut="EN_ATTENTE",
            reference=reference,
        )

        paiement.commandes.set(commandes)

        resultat = creer_facture_commande(
            paiement=paiement,
            commandes=commandes,
        )

        if not resultat.get("success"):
            paiement.statut = "ECHEC"
            paiement.save(
                update_fields=[
                    "statut",
                    "date_modification",
                ]
            )

            return Response(
                {
                    "success": False,
                    "message": resultat.get(
                        "message",
                        "Impossible de créer la facture PayDunya."
                    )
                },
                status=502
            )

        return Response(
            {
                "success": True,
                "message": "Paiement initialisé avec succès.",
                "paiement": {
                    "id": paiement.id,
                    "reference": paiement.reference,
                    "montant": str(paiement.montant),
                    "statut": paiement.statut,
                },
                "checkout_url": resultat["url_paiement"],
            },
            status=201
        )
        



class CompteReversementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Récupère le compte de reversement
        de l'agronome connecté.
        """

        if request.user.role != "AGRONOME":
            return Response(
                {
                    "success": False,
                    "message": "Accès réservé aux agronomes."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            compte = CompteReversement.objects.get(
                utilisateur=request.user
            )

        except CompteReversement.DoesNotExist:
            return Response(
                {
                    "success": True,
                    "compte": None,
                },
                status=status.HTTP_200_OK,
            )

        serializer = CompteReversementSerializer(compte)

        return Response(
            {
                "success": True,
                "compte": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """
        Crée ou met à jour le compte de reversement
        de l'agronome connecté.
        """

        if request.user.role != "AGRONOME":
            return Response(
                {
                    "success": False,
                    "message": "Accès réservé aux agronomes."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        account_alias = request.data.get("account_alias")

        if not account_alias:
            return Response(
                {
                    "success": False,
                    "message": "L'identifiant PayDunya est obligatoire."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        account_alias = str(account_alias).strip()

        if not account_alias:
            return Response(
                {
                    "success": False,
                    "message": "L'identifiant PayDunya est obligatoire."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        compte, created = CompteReversement.objects.update_or_create(
            utilisateur=request.user,
            defaults={
                "account_alias": account_alias,
                "actif": True,
            },
        )

        serializer = CompteReversementSerializer(compte)

        return Response(
            {
                "success": True,
                "message": (
                    "Compte de reversement enregistré."
                    if created
                    else "Compte de reversement mis à jour."
                ),
                "compte": serializer.data,
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )
        
        
class MonAbonnementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        utilisateur = request.user

        if utilisateur.role != "AGRONOME":
            return Response(
                {
                    "success": False,
                    "message": "Accès réservé aux agronomes."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        abonnement = (
            AbonnementAgronome.objects
            .filter(agronome=utilisateur)
            .order_by("-date_creation")
            .first()
        )

        if not abonnement:
            return Response(
                {
                    "success": True,
                    "abonnement": None,
                    "paiement_actuel": None,
                    "historique": [],
                },
                status=status.HTTP_200_OK,
            )

        paiements = (
            Paiement.objects
            .filter(
                utilisateur=utilisateur,
                type_paiement="ABONNEMENT",
            )
            .order_by("-date_creation")
        )

        dernier_paiement = paiements.first()

        historique = []

        for paiement in paiements:
            historique.append(
                {
                    "id": paiement.id,
                    "reference": paiement.reference,
                    "montant": str(paiement.montant),
                    "statut": paiement.statut,
                    "statut_display": paiement.get_statut_display(),
                    "date_creation": paiement.date_creation,
                    "date_paiement": paiement.date_paiement,
                }
            )

        return Response(
            {
                "success": True,

                "abonnement": {
                    "id": abonnement.id,
                    "type": abonnement.type_abonnement,
                    "type_display": abonnement.get_type_abonnement_display(),
                    "date_debut": abonnement.date_debut,
                    "date_fin": abonnement.date_fin,
                    "statut": abonnement.statut,
                    "statut_display": abonnement.get_statut_display(),
                    "statut_paiement": abonnement.statut_paiement,
                    "statut_paiement_display": (
                        abonnement.get_statut_paiement_display()
                    ),
                },

                "paiement_actuel": (
                    {
                        "montant": str(dernier_paiement.montant),
                        "statut": dernier_paiement.statut,
                        "date_paiement": dernier_paiement.date_paiement,
                    }
                    if dernier_paiement
                    else None
                ),

                "historique": historique,
            },
            status=status.HTTP_200_OK,
        )