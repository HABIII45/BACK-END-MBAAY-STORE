import secrets
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from paniers.models import Panier
from livraisons.models import ModeLivraison

from .models import Commande, LigneCommande
from .serializers import CommandeSerializer,CommandeSuiviSerializer,CommandeAgronomeSerializer
from paiements.models import Reversement
from paiements.services.paydunya import effectuer_reversement
from utilisateurs.permissions import IsAgronomeMBAAY
class CreerCommandeView(APIView):
    """
    Crée une ou plusieurs commandes à partir du panier.

    Un panier peut contenir des produits provenant
    de plusieurs boutiques.

    Une commande est donc créée pour chaque boutique.
    """

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):

        panier_id = request.headers.get("X-Panier-ID")

        if not panier_id:
            return Response(
                {
                    "success": False,
                    "message": "Identifiant du panier manquant."
                },
                status=400
            )

        try:
            panier = (
                Panier.objects
                .prefetch_related(
                    "lignes__produit__boutique",
                    "lignes__produit__unite_vente",
                )
                .get(identifiant=panier_id)
            )

        except (Panier.DoesNotExist, ValueError):

            return Response(
                {
                    "success": False,
                    "message": "Panier introuvable."
                },
                status=404
            )

        lignes_panier = list(panier.lignes.all())

        if not lignes_panier:

            return Response(
                {
                    "success": False,
                    "message": "Votre panier est vide."
                },
                status=400
            )

        # --------------------------------------------------
        # 1. RÉCUPÉRER LES MODES DE LIVRAISON
        # --------------------------------------------------

        modes_livraison = request.data.get("modes_livraison", {})

        if not isinstance(modes_livraison, dict):

            return Response(
                {
                    "success": False,
                    "message": "Les modes de livraison sont invalides."
                },
                status=400
            )

        # --------------------------------------------------
        # 2. REGROUPER LES PRODUITS PAR BOUTIQUE
        # --------------------------------------------------

        lignes_par_boutique = {}

        for ligne in lignes_panier:
    
             produit = ligne.produit
             boutique = produit.boutique

             if boutique.id not in lignes_par_boutique:
                lignes_par_boutique[boutique.id] = {
                  "boutique": boutique,
                   "lignes": []
                }

             lignes_par_boutique[boutique.id]["lignes"].append(
               ligne
            )

        commandes_creees = []

        # --------------------------------------------------
        # 3. CRÉER UNE COMMANDE POUR CHAQUE BOUTIQUE
        # --------------------------------------------------

        for boutique_id, donnees in lignes_par_boutique.items():

            boutique = donnees["boutique"]
            lignes = donnees["lignes"]
            if boutique.statut != "PUBLIEE":
             return Response(
              {
                "success": False,
                 "message": (
                   f"La boutique « {boutique.nom} » "
                   "n'est pas disponible actuellement."
                 )
             },
              status=400
             )

            # ----------------------------------------------
            # Vérifier la configuration de livraison
            # ----------------------------------------------

            try:
                configuration = boutique.configuration_livraison

            except Exception:

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"La boutique « {boutique.nom} » "
                            "n'a pas configuré sa livraison."
                        )
                    },
                    status=400
                )

            # ----------------------------------------------
            # Récupérer le mode choisi pour cette boutique
            # ----------------------------------------------

            mode_id = modes_livraison.get(str(boutique.id))

            if not mode_id:

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"Veuillez choisir un mode de livraison "
                            f"pour la boutique « {boutique.nom} »."
                        )
                    },
                    status=400
                )

            try:

                mode_livraison = ModeLivraison.objects.get(
                    id=mode_id,
                    active=True
                )

            except ModeLivraison.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Le mode de livraison sélectionné "
                            "n'est pas disponible."
                        )
                    },
                    status=400
                )

            # ----------------------------------------------
            # Vérifier que la boutique autorise ce mode
            # ----------------------------------------------

            if not configuration.modes_livraison.filter(
                id=mode_livraison.id
            ).exists():

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"Le mode « {mode_livraison.nom} » "
                            f"n'est pas proposé par "
                            f"« {boutique.nom} »."
                        )
                    },
                    status=400
                )

            # ----------------------------------------------
            # Calcul du sous-total
            # ----------------------------------------------

            sous_total = Decimal("0.00")

            for ligne in lignes:
    
                produit = (
                ligne.produit.__class__.objects
                .select_for_update()
                .get(pk=ligne.produit.pk)
                )

                # Vérifier disponibilité
                if not produit.disponible:

                    return Response(
                        {
                            "success": False,
                            "message": (
                                f"Le produit « {produit.nom} » "
                                "n'est plus disponible."
                            )
                        },
                        status=400
                    )

                # Vérifier stock
                if ligne.quantite > produit.stock_actuel:

                    return Response(
                        {
                            "success": False,
                            "message": (
                                f"Le stock disponible pour "
                                f"« {produit.nom} » est insuffisant."
                            )
                        },
                        status=400
                    )

                sous_total += (
                    ligne.quantite * ligne.prix_unitaire
                )

            # ----------------------------------------------
            # Calcul des frais de livraison
            # ----------------------------------------------

            frais_livraison = Decimal("0.00")

            if mode_livraison.code == "ACHETEUR_LIVREUR":

                # L'acheteur fournit son propre livreur.
                # MBAAY ne facture donc pas de livraison.

                frais_livraison = Decimal("0.00")

            elif mode_livraison.code == "AGRONOME_LIVREUR":

                if configuration.type_tarification == "FIXE":

                    frais_livraison = (
                        configuration.frais_livraison_fixe
                    )

                elif configuration.type_tarification == "DISTANCE":

                    # Le calcul selon la distance sera ajouté
                    # lorsque nous intégrerons la géolocalisation
                    # de l'acheteur.

                    return Response(
                        {
                            "success": False,
                            "message": (
                                "Le calcul de livraison selon "
                                "la distance sera disponible "
                                "avec la géolocalisation."
                            )
                        },
                        status=400
                    )

            # ----------------------------------------------
            # Total
            # ----------------------------------------------

            total = sous_total + frais_livraison

            # ----------------------------------------------
            # Génération des informations de commande
            # ----------------------------------------------

            reference = (
                f"MBAAY-{secrets.token_hex(5).upper()}"
            )

            token_suivi = secrets.token_urlsafe(32)

            code_reception = str(
                secrets.randbelow(900000) + 100000
            )

            # ----------------------------------------------
            # Création de la commande
            # ----------------------------------------------

            commande = Commande.objects.create(
                boutique=boutique,
                mode_livraison=mode_livraison,
                reference=reference,
                token_suivi=token_suivi,
                code_reception=code_reception,
                statut="EN_ATTENTE_PAIEMENT",
                sous_total=sous_total,
                frais_livraison=frais_livraison,
                total=total,
            )

            # ----------------------------------------------
            # Création des lignes de commande
            # ----------------------------------------------

            for ligne in lignes:

                LigneCommande.objects.create(
                    commande=commande,
                    produit=ligne.produit,
                    quantite=ligne.quantite,
                    prix_unitaire=ligne.prix_unitaire,
                    total=(
                        ligne.quantite *
                        ligne.prix_unitaire
                    ),
                )

            commandes_creees.append(commande)

        # --------------------------------------------------
        # 4. VIDER LE PANIER
        # --------------------------------------------------

        panier.lignes.all().delete()

        # --------------------------------------------------
        # 5. RÉPONSE
        # --------------------------------------------------

        serializer = CommandeSerializer(
            commandes_creees,
            many=True
        )

        return Response(
            {
                "success": True,
                "message": "Commande(s) créée(s) avec succès.",
                "commandes": serializer.data,
            },
            status=201
        )


class SuiviCommandeView(APIView):
    """
    Permet à l'acheteur de consulter sa commande
    grâce à son token de suivi.

    Aucun compte n'est nécessaire.
    """

    permission_classes = [AllowAny]

    def get(self, request, token_suivi):

        try:
            commande = (
                Commande.objects
                .select_related(
                    "boutique",
                    "mode_livraison",
                )
                .prefetch_related(
                    "lignes__produit"
                )
                .get(token_suivi=token_suivi)
            )

        except Commande.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Commande introuvable."
                },
                status=404
            )

        serializer = CommandeSuiviSerializer(commande)

        return Response(
            {
                "success": True,
                "commande": serializer.data,
            },
            status=200
        )


class ConfirmerReceptionCommandeView(APIView):
    """
    Permet à l'acheteur de confirmer la réception
    de sa commande avec son code de réception.
    """

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, token_suivi):

        code_reception = request.data.get("code_reception")

        if not code_reception:
            return Response(
                {
                    "success": False,
                    "message": "Le code de réception est obligatoire."
                },
                status=400
            )

        code_reception = str(code_reception).strip()

        # --------------------------------------------------
        # 1. RÉCUPÉRER LA COMMANDE
        # --------------------------------------------------

        try:
            commande = (
                Commande.objects
                .select_for_update()
                .select_related(
                    "boutique__proprietaire"
                )
                .get(token_suivi=token_suivi)
            )

        except Commande.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Commande introuvable."
                },
                status=404
            )

        # --------------------------------------------------
        # 2. VÉRIFIER SI DÉJÀ LIVRÉE
        # --------------------------------------------------

        if commande.statut == "LIVREE":
            return Response(
                {
                    "success": False,
                    "message": "Cette commande a déjà été livrée."
                },
                status=400
            )

        # --------------------------------------------------
        # 3. VÉRIFIER LE STATUT
        # --------------------------------------------------

        if commande.statut != "EN_LIVRAISON":
            return Response(
                {
                    "success": False,
                    "message": (
                        "La réception ne peut être confirmée "
                        "que lorsque la commande est en livraison."
                    )
                },
                status=400
            )

        # --------------------------------------------------
        # 4. VÉRIFIER LE CODE
        # --------------------------------------------------

        if code_reception != commande.code_reception:
            return Response(
                {
                    "success": False,
                    "message": "Code de réception incorrect."
                },
                status=400
            )

        # --------------------------------------------------
        # 5. CONFIRMER LA LIVRAISON
        # --------------------------------------------------

        commande.statut = "LIVREE"
        commande.date_livraison = timezone.now()

        commande.save(
            update_fields=[
                "statut",
                "date_livraison",
                "date_modification",
            ]
        )

        # --------------------------------------------------
        # 6. RÉCUPÉRER L'AGRONOME
        # --------------------------------------------------

        agronome = commande.boutique.proprietaire

        try:
            compte_reversement = agronome.compte_reversement

        except Exception:
            return Response(
                {
                    "success": True,
                    "message": (
                        "Réception confirmée, "
                        "mais aucun compte de reversement "
                        "n'est configuré pour cet agronome."
                    ),
                    "commande": {
                        "reference": commande.reference,
                        "statut": commande.statut,
                        "date_livraison": commande.date_livraison,
                    },
                },
                status=200
            )

        # --------------------------------------------------
        # 7. CRÉER LE REVERSEMENT
        # --------------------------------------------------

        reversement, created = Reversement.objects.get_or_create(
            commande=commande,
            defaults={
                "agronome": agronome,
                "compte_reversement": compte_reversement,
                "montant": commande.total,
                "reference": (
                    f"MBAAY-REV-"
                    f"{secrets.token_hex(5).upper()}"
                ),
                "statut": "EN_ATTENTE",
            }
        )

        # --------------------------------------------------
        # 8. EFFECTUER LE REVERSEMENT
        # --------------------------------------------------

        if created:

            resultat = effectuer_reversement(reversement)

            if not resultat.get("success"):

                return Response(
                    {
                        "success": True,
                        "message": (
                            "Réception confirmée, "
                            "mais le reversement a échoué."
                        ),
                        "commande": {
                            "reference": commande.reference,
                            "statut": commande.statut,
                            "date_livraison": commande.date_livraison,
                        },
                        "reversement": {
                            "statut": reversement.statut,
                            "reference": reversement.reference,
                        },
                    },
                    status=200
                )

        # --------------------------------------------------
        # 9. SUCCÈS
        # --------------------------------------------------

        return Response(
            {
                "success": True,
                "message": (
                    "Réception confirmée et reversement "
                    "effectué avec succès."
                ),
                "commande": {
                    "reference": commande.reference,
                    "statut": commande.statut,
                    "date_livraison": commande.date_livraison,
                },
                "reversement": {
                    "statut": reversement.statut,
                    "reference": reversement.reference,
                },
            },
            status=200
        )
        
        
class MesCommandesAgronomeView(APIView):
    """
    Permet à un agronome de consulter les commandes
    de ses boutiques.
    """

    permission_classes = [
        IsAuthenticated,
        IsAgronomeMBAAY,
    ]

    def get(self, request):

        commandes = (
            Commande.objects
            .filter(
                boutique__proprietaire=request.user
            )
            .select_related(
                "boutique",
                "mode_livraison",
            )
            .prefetch_related(
                "lignes__produit__unite_vente"
            )
            .order_by("-date_creation")
        )

        serializer = CommandeAgronomeSerializer(
            commandes,
            many=True
        )

        return Response(
            {
                "success": True,
                "nombre": commandes.count(),
                "commandes": serializer.data,
            },
            status=200
        )
        
class DetailCommandeAgronomeView(APIView):
    """
    Permet à un agronome de consulter
    le détail d'une de ses commandes.
    """

    permission_classes = [
        IsAuthenticated,
        IsAgronomeMBAAY,
    ]

    def get(self, request, commande_id):

        commande = get_object_or_404(
            Commande.objects
            .select_related(
                "boutique",
                "mode_livraison",
            )
            .prefetch_related(
                "lignes__produit__unite_vente"
            ),
            id=commande_id,
            boutique__proprietaire=request.user,
        )

        serializer = CommandeAgronomeSerializer(
            commande
        )

        return Response(
            {
                "success": True,
                "commande": serializer.data,
            },
            status=200
        )
        
class AvancerCommandeAgronomeView(APIView):
    """
    Permet à l'agronome de faire avancer
    une commande à l'étape suivante.
    """

    permission_classes = [
        IsAuthenticated,
        IsAgronomeMBAAY,
    ]

    STATUT_SUIVANT = {
        "PAYEE": "EN_PREPARATION",
        "EN_PREPARATION": "PRETE",
        "PRETE": "EN_LIVRAISON",
    }

    @transaction.atomic
    def post(self, request, commande_id):

        commande = get_object_or_404(
            Commande.objects
            .select_for_update()
            .select_related(
                "boutique",
                "mode_livraison",
            ),
            id=commande_id,
            boutique__proprietaire=request.user,
        )

        statut_actuel = commande.statut

        if statut_actuel not in self.STATUT_SUIVANT:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Cette commande ne peut pas "
                        "être avancée depuis son statut actuel."
                    ),
                    "statut": statut_actuel,
                },
                status=400
            )

        nouveau_statut = self.STATUT_SUIVANT[
            statut_actuel
        ]

        commande.statut = nouveau_statut

        commande.save(
            update_fields=[
                "statut",
                "date_modification",
            ]
        )

        serializer = CommandeAgronomeSerializer(
            commande
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Le statut de la commande a été mis à jour."
                ),
                "ancien_statut": statut_actuel,
                "nouveau_statut": nouveau_statut,
                "commande": serializer.data,
            },
            status=200
        )