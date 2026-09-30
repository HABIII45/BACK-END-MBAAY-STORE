from decimal import Decimal
from datetime import timedelta
import secrets

from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils.text import slugify
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from utilisateurs.permissions import IsAgronomeMBAAY

from .models import Boutique

from .serializers import (
    BoutiqueSerializer,
    CreationEspaceSerializer,
    BoutiqueAcheteurSerializer,
    BoutiqueRechercheAcheteurSerializer,
    BoutiquePubliqueSerializer,
)

from produits.models import Produit
from categories.models import MoyenPaiement

from utilisateurs.models import Utilisateur, VerificationEmail


def generer_slug_unique(nom):
    """
    Génère automatiquement un slug unique à partir du nom de la boutique.

    Exemple :
    Agro Sénégal → agro-senegal
    Agro Sénégal → agro-senegal-2
    Agro Sénégal → agro-senegal-3
    """

    slug_base = slugify(nom)
    slug = slug_base
    compteur = 2

    while Boutique.objects.filter(slug=slug).exists():
        slug = f"{slug_base}-{compteur}"
        compteur += 1

    return slug


class BoutiqueViewSet(viewsets.ModelViewSet):

    queryset = Boutique.objects.all()
    serializer_class = BoutiqueSerializer

    # =====================================================
    # PERMISSIONS
    # =====================================================

    def get_permissions(self):

        if self.action in [
            "creation_espace",
            "marche",
            "recherche",
            "publique",
        ]:
            return [AllowAny()]

        return [
            IsAuthenticated(),
            IsAgronomeMBAAY(),
        ]

    def get_queryset(self):

        if self.action in [
            "marche",
            "recherche",
            "creation_espace",
            "publique",
        ]:
            return Boutique.objects.all()

        if (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.role == "AGRONOME"
        ):
            return Boutique.objects.filter(
                proprietaire=self.request.user
            )

        return Boutique.objects.none()

    # =====================================================
    # SERIALIZER UTILISÉ SELON L'ACTION
    # =====================================================

    def get_serializer_class(self):

        if self.action == "creation_espace":
            return CreationEspaceSerializer

        if self.action == "marche":
            return BoutiqueAcheteurSerializer

        if self.action == "recherche":
            return BoutiqueRechercheAcheteurSerializer

        if self.action == "publique":
            return BoutiquePubliqueSerializer

        return BoutiqueSerializer

    # =====================================================
    # MARCHÉ
    # GET /api/boutiques/marche/
    # =====================================================

    @action(
        detail=False,
        methods=["get"],
        url_path="marche"
    )
    def marche(self, request):

        boutiques = (
            Boutique.objects
            .filter(
                statut="PUBLIEE"
            )
            .order_by("-date_creation")
        )

        serializer = BoutiqueAcheteurSerializer(
            boutiques,
            many=True,
            context={
                "request": request
            }
        )

        return Response(
            {
                "success": True,
                "nombre": boutiques.count(),
                "boutiques": serializer.data
            }
        )

    # =====================================================
    # RECHERCHE ACHETEUR
    # POST /api/boutiques/recherche/
    # =====================================================

    @action(
        detail=False,
        methods=["post"],
        url_path="recherche"
    )
    def recherche(self, request):

        # =================================================
        # 1. RÉCUPÉRATION DES CRITÈRES
        # =================================================

        criteres = request.data.get(
            "criteres",
            {}
        )

        if not isinstance(criteres, dict):

            return Response(
                {
                    "success": False,
                    "message": (
                        "Les critères de recherche "
                        "sont invalides."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =================================================
        # 2. EXTRACTION DES CRITÈRES
        # =================================================

        mot_cle = criteres.get(
            "mot_cle"
        )

        categorie = criteres.get(
            "categorie"
        )

        prix_min = criteres.get(
            "prix_min"
        )

        prix_max = criteres.get(
            "prix_max"
        )

        quantite = criteres.get(
            "quantite"
        )

        unite = criteres.get(
            "unite"
        )

        qualite = criteres.get(
            "qualite"
        )

        # =================================================
        # 3. PRODUITS DE BASE
        # =================================================

        produits = (
            Produit.objects
            .filter(
                disponible=True,
                stock_actuel__gt=0,
                boutique__statut="PUBLIEE"
            )
            .select_related(
                "boutique",
                "categorie",
                "unite_vente"
            )
        )

        # =================================================
        # 4. RECHERCHE PAR MOT-CLÉ
        # =================================================

        if mot_cle:

            produits = produits.filter(
                Q(
                    nom__icontains=mot_cle
                )
                |
                Q(
                    description__icontains=mot_cle
                )
            )

        # =================================================
        # 5. RECHERCHE PAR CATÉGORIE
        # =================================================

        if categorie:

            produits = produits.filter(
                categorie__nom__icontains=categorie
            )

        # =================================================
        # 6. PRIX MINIMUM
        # =================================================

        if prix_min is not None:

            try:

                prix_min = Decimal(
                    str(prix_min)
                )

                produits = produits.filter(
                    prix__gte=prix_min
                )

            except (
                ValueError,
                TypeError
            ):
                pass

        # =================================================
        # 7. PRIX MAXIMUM
        # =================================================

        if prix_max is not None:

            try:

                prix_max = Decimal(
                    str(prix_max)
                )

                produits = produits.filter(
                    prix__lte=prix_max
                )

            except (
                ValueError,
                TypeError
            ):
                pass

        # =================================================
        # 8. UNITÉ DE VENTE
        # =================================================

        if unite:

            produits = produits.filter(
                Q(
                    unite_vente__symbole__iexact=unite
                )
                |
                Q(
                    unite_vente__nom__icontains=unite
                )
            )

        # =================================================
        # 9. QUANTITÉ DISPONIBLE
        # =================================================

        if quantite is not None:

            try:

                quantite = Decimal(
                    str(quantite)
                )

                produits = produits.filter(
                    stock_actuel__gte=quantite
                )

            except (
                ValueError,
                TypeError
            ):
                pass

        # =================================================
        # 10. QUALITÉ
        # =================================================

        if qualite:

            produits = produits.filter(
                Q(
                    nom__icontains=qualite
                )
                |
                Q(
                    description__icontains=qualite
                )
            )

        # =================================================
        # 11. SUPPRESSION DES DOUBLONS
        # =================================================

        produits = produits.distinct()

        # =================================================
        # 12. IDENTIFIANTS DES BOUTIQUES
        # =================================================

        boutique_ids = (
            produits
            .values_list(
                "boutique_id",
                flat=True
            )
            .distinct()
        )

        # =================================================
        # 13. PRÉPARATION DES PRODUITS CORRESPONDANTS
        # =================================================

        produits_correspondants = (
            produits
            .order_by("-date_creation")
        )

        # =================================================
        # 14. RÉCUPÉRATION DES BOUTIQUES
        # =================================================

        boutiques = (
            Boutique.objects
            .filter(
                id__in=boutique_ids,
                statut="PUBLIEE"
            )
            .prefetch_related(
                Prefetch(
                    "produits",
                    queryset=produits_correspondants,
                    to_attr="produits_correspondants"
                )
            )
            .order_by("-date_creation")
        )

        # =================================================
        # 15. SERIALIZATION
        # =================================================

        serializer = (
            BoutiqueRechercheAcheteurSerializer(
                boutiques,
                many=True,
                context={
                    "request": request
                }
            )
        )

        # =================================================
        # 16. RÉPONSE
        # =================================================

        return Response(
            {
                "success": True,
                "nombre_resultats": boutiques.count(),
                "resultats": serializer.data
            },
            status=status.HTTP_200_OK
        )

    # =====================================================
    # CRÉATION ESPACE AGRONOME
    # POST /api/boutiques/creation-espace/
    # =====================================================

    @action(
        detail=False,
        methods=["post"],
        url_path="creation-espace"
    )
    def creation_espace(self, request):

        # =================================================
        # 1. VALIDATION DES DONNÉES
        # =================================================

        serializer = CreationEspaceSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        # =================================================
        # 2. CRÉATION DU COMPTE + VÉRIFICATION + BOUTIQUE
        # =================================================

        with transaction.atomic():

            # ---------------------------------------------
            # Création du compte agronome
            # ---------------------------------------------

            utilisateur = Utilisateur.objects.create_user(
                email=data["email"],
                nom=data["nom"],
                prenom=data["prenom"],
                telephone=data["telephone"],
            )

            # ---------------------------------------------
            # Génération du token
            # ---------------------------------------------

            token = secrets.token_urlsafe(32)

            # ---------------------------------------------
            # Enregistrement du token
            # ---------------------------------------------

            verification = VerificationEmail.objects.create(
                utilisateur=utilisateur,
                token=token,
                date_expiration=(
                    timezone.now()
                    + timedelta(hours=1)
                )
            )

            # ---------------------------------------------
            # Génération du lien
            # ---------------------------------------------

            lien_verification = (
                f"{settings.FRONTEND_URL}"
                f"/connexion/agronome/verification"
                f"?token={verification.token}"
            )

            # ---------------------------------------------
            # Envoi de l'e-mail
            # ---------------------------------------------

            send_mail(
                subject=(
                    "Vérification de votre adresse e-mail "
                    "- MBAAY STORE"
                ),

                message=f"""
Bonjour {utilisateur.prenom},

Votre espace MBAAY STORE est presque prêt.

Pour confirmer votre adresse e-mail, cliquez sur le lien suivant :

{lien_verification}

Ce lien est valable pendant 30 minutes.

Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet e-mail.

L'équipe MBAAY STORE
""",

                from_email=settings.DEFAULT_FROM_EMAIL,

                recipient_list=[
                    utilisateur.email
                ],
            )

            # ---------------------------------------------
            # Création de la boutique
            # ---------------------------------------------

            boutique = Boutique.objects.create(
                proprietaire=utilisateur,
                nom=data["nom_boutique"],
                slug=generer_slug_unique(
                    data["nom_boutique"]
                ),
                description=data[
                    "description_boutique"
                ],
                latitude=data["latitude"],
                longitude=data["longitude"]
            )

        # =================================================
        # 3. RÉPONSE AU FRONTEND
        # =================================================

        return Response(
            {
                "message": (
                    "Votre espace est presque prêt. "
                    "Un lien de vérification a été envoyé "
                    "à votre adresse e-mail."
                ),

                "utilisateur": {
                    "id": utilisateur.id,
                    "prenom": utilisateur.prenom,
                    "nom": utilisateur.nom,
                    "email": utilisateur.email,
                    "telephone": utilisateur.telephone,
                },

                "boutique": BoutiqueSerializer(
                    boutique
                ).data
            },

            status=status.HTTP_201_CREATED
        )

    # =====================================================
    # MOYENS DE PAIEMENT DE MA BOUTIQUE
    # PATCH /api/boutiques/ma-boutique/paiements/
    # =====================================================

    @action(
        detail=False,
        methods=["patch"],
        url_path="ma-boutique/paiements"
    )
    def modifier_moyens_paiement(self, request):

        # =================================================
        # 1. RÉCUPÉRER LA BOUTIQUE DE L'AGRONOME CONNECTÉ
        # =================================================

        try:
            boutique = request.user.boutique
        except Boutique.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Aucune boutique associée à votre compte."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # =================================================
        # 2. RÉCUPÉRER LES IDS ENVOYÉS PAR LE FRONTEND
        # =================================================

        moyens_paiement_ids = request.data.get(
            "moyens_paiement"
        )

        if not isinstance(moyens_paiement_ids, list):
            return Response(
                {
                    "success": False,
                    "message": (
                        "Les moyens de paiement doivent être "
                        "envoyés sous forme de liste."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =================================================
        # 3. RÉCUPÉRER LES MOYENS DE PAIEMENT
        # =================================================

        moyens_paiement = MoyenPaiement.objects.filter(
            id__in=moyens_paiement_ids,
            active=True
        )

        # =================================================
        # 4. VÉRIFIER QUE TOUS LES IDS EXISTENT
        # =================================================

        if moyens_paiement.count() != len(
            set(moyens_paiement_ids)
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "Un ou plusieurs moyens de paiement "
                        "sont invalides ou désactivés."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =================================================
        # 5. ENREGISTRER LES MOYENS DE PAIEMENT
        # =================================================

        boutique.moyens_paiement.set(
            moyens_paiement
        )

        # =================================================
        # 6. RÉPONSE
        # =================================================

        return Response(
            {
                "success": True,
                "message": (
                    "Les moyens de paiement ont été "
                    "enregistrés avec succès."
                ),
                "moyens_paiement": [
                    {
                        "id": moyen.id,
                        "nom": moyen.nom,
                        "code": moyen.code,
                    }
                    for moyen in moyens_paiement
                ]
            },
            status=status.HTTP_200_OK
        )

    # =====================================================
    # IDENTITÉ DE MA BOUTIQUE
    # PATCH /api/boutiques/ma-boutique/identite/
    # =====================================================

    @action(
        detail=False,
        methods=["patch"],
        url_path="ma-boutique/identite"
    )
    def modifier_identite(self, request):

        # =================================================
        # 1. RÉCUPÉRER LA BOUTIQUE DE L'AGRONOME CONNECTÉ
        # =================================================

        try:
            boutique = request.user.boutique

        except Boutique.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Aucune boutique associée à votre compte."
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # =================================================
        # 2. LOGO
        # =================================================

        if "logo" in request.FILES:
            boutique.logo = request.FILES["logo"]

        # =================================================
        # 3. IMAGE / COUVERTURE
        # =================================================

        if "image" in request.FILES:
            boutique.image = request.FILES["image"]

        # =================================================
        # 4. PHOTO DE L'AGRONOME
        # =================================================

        if "photo_agronome" in request.FILES:
            boutique.photo_agronome = (
                request.FILES["photo_agronome"]
            )

        # =================================================
        # 5. COULEUR PRINCIPALE
        # =================================================

        couleur = request.data.get(
            "couleur_principale"
        )

        if couleur is not None:
            boutique.couleur_principale = couleur

        # =================================================
        # 6. PALETTE
        # =================================================

        palette = request.data.get(
            "palette"
        )

        if palette is not None:
            boutique.palette = palette

        # =================================================
        # 7. TIKTOK
        # =================================================

        tiktok = request.data.get(
            "tiktok"
        )

        if tiktok is not None:
            boutique.tiktok = tiktok

        # =================================================
        # 8. FACEBOOK
        # =================================================

        facebook = request.data.get(
            "facebook"
        )

        if facebook is not None:
            boutique.facebook = facebook

        # =================================================
        # 9. SAUVEGARDE
        # =================================================

        boutique.save()

        # =================================================
        # 10. RÉPONSE
        # =================================================

        return Response(
            {
                "success": True,
                "message": (
                    "L'identité de votre boutique "
                    "a été enregistrée."
                ),
                "boutique": BoutiqueSerializer(
                    boutique,
                    context={
                        "request": request
                    }
                ).data
            },
            status=status.HTTP_200_OK
        )

    # =====================================================
    # BOUTIQUE PUBLIQUE
    # GET /api/boutiques/publique/<slug>/
    # =====================================================

    @action(
        detail=False,
        methods=["get"],
        url_path=r"publique/(?P<slug>[-\w]+)"
    )
    def publique(self, request, slug=None):

        try:
            boutique = (
                Boutique.objects
                .prefetch_related(
                    "moyens_paiement"
                )
                .get(
                    slug=slug,
                    statut="PUBLIEE"
                )
            )

        except Boutique.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Cette boutique n'existe pas "
                        "ou n'est pas publiée."
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BoutiquePubliqueSerializer(
            boutique,
            context={
                "request": request
            }
        )

        return Response(
            {
                "success": True,
                "boutique": serializer.data
            },
            status=status.HTTP_200_OK
        )

    # =====================================================
    # PUBLICATION DE MA BOUTIQUE
    # POST /api/boutiques/ma-boutique/publier/
    # =====================================================

    @action(
        detail=False,
        methods=["post"],
        url_path="ma-boutique/publier"
    )
    def publier(self, request):

        # =================================================
        # 1. RÉCUPÉRER LA BOUTIQUE DE L'AGRONOME CONNECTÉ
        # =================================================

        try:
            boutique = request.user.boutique

        except Boutique.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Aucune boutique associée à votre compte."
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # =================================================
        # 2. VÉRIFIER QUE LA BOUTIQUE EST PRÊTE
        # =================================================

        if boutique.statut == "PUBLIEE":
            return Response(
                {
                    "success": False,
                    "message": "Votre boutique est déjà publiée."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =================================================
        # 3. PUBLIER LA BOUTIQUE
        # =================================================

        boutique.statut = "PUBLIEE"

        boutique.save(
            update_fields=[
                "statut",
                "date_modification"
            ]
        )

        # =================================================
        # 4. GÉNÉRER LE LIEN PUBLIC DE LA BOUTIQUE
        # =================================================

        lien_public = (
            f"{settings.FRONTEND_URL}"
            f"/boutique/{boutique.slug}"
        )

        # =================================================
        # 5. RÉPONSE
        # =================================================

        return Response(
            {
                "success": True,
                "message": (
                    "Votre boutique a été publiée avec succès."
                ),
                "boutique": BoutiqueSerializer(
                    boutique,
                    context={
                        "request": request
                    }
                ).data,
                "lien_public": lien_public,
            },
            status=status.HTTP_200_OK
        )