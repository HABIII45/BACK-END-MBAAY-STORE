from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .serializers import AdminLoginSerializer

from django.utils import timezone
import secrets

from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken

from .models import VerificationEmail, LienConnexion, Utilisateur
from django.db import transaction
class AdminLoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = AdminLoginSerializer(
            data=request.data
        )

        if serializer.is_valid():

            user = serializer.validated_data["user"]

            return Response(
                {
                    "message": "Connexion administrateur réussie.",
                    "access": str(
                        serializer.validated_data["access"]
                    ),
                    "refresh": str(
                        serializer.validated_data["refresh"]
                    ),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "nom": user.nom,
                        "prenom": user.prenom,
                        "role": user.role,
                        "is_staff": user.is_staff,
                        "is_superuser": user.is_superuser,
                    }
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
  

class DemanderLienConnexionView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        email = request.data.get("email")

        # =============================================
        # VÉRIFICATION DE L'EMAIL
        # =============================================

        if not email:
            return Response(
                {
                    "message": "L'adresse e-mail est obligatoire."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        email = email.strip().lower()

        # =============================================
        # RECHERCHE DU COMPTE
        # =============================================

        try:
            utilisateur = Utilisateur.objects.get(
                email=email
            )

        except Utilisateur.DoesNotExist:

            return Response(
                {
                    "message": (
                        "Aucun compte MBAAY STORE n'est "
                        "associé à cette adresse e-mail."
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # =============================================
        # VÉRIFICATION DU RÔLE
        # =============================================

        if utilisateur.role != "AGRONOME":

            return Response(
                {
                    "message": (
                        "Cette adresse e-mail n'est pas "
                        "associée à un compte agronome."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # =============================================
        # VÉRIFICATION DE L'EMAIL
        # =============================================

        if not utilisateur.email_verifie:

            return Response(
                {
                    "message": (
                        "L'adresse e-mail de ce compte "
                        "n'a pas encore été vérifiée."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =============================================
        # CRÉATION DU TOKEN
        # =============================================

        token = secrets.token_urlsafe(48)

        # =============================================
        # EXPIRATION : 15 MINUTES
        # =============================================

        date_expiration = (
            timezone.now() + timedelta(minutes=15)
        )

        # =============================================
        # CRÉATION DU LIEN
        # =============================================

        lien = LienConnexion.objects.create(
            utilisateur=utilisateur,
            token=token,
            date_expiration=date_expiration,
        )

        # =============================================
        # URL FRONTEND
        # =============================================

        lien_connexion = (
            f"{settings.FRONTEND_URL}"
            f"/connexion/agronome"
            f"?token={lien.token}"
        )

        # =============================================
        # ENVOI DE L'EMAIL
        # =============================================

        send_mail(
            subject="Votre lien de connexion — MBAAY STORE",

            message=(
                f"Bonjour {utilisateur.prenom},\n\n"
                "Vous avez demandé à vous connecter "
                "à votre espace MBAAY STORE.\n\n"
                "Cliquez sur le lien suivant pour vous connecter :\n\n"
                f"{lien_connexion}\n\n"
                "Ce lien est valable pendant 15 minutes "
                "et ne peut être utilisé qu'une seule fois.\n\n"
                "Si vous n'êtes pas à l'origine de cette demande, "
                "vous pouvez ignorer cet e-mail.\n\n"
                "MBAAY STORE"
            ),

            from_email=settings.DEFAULT_FROM_EMAIL,

            recipient_list=[
                utilisateur.email
            ],

            fail_silently=False,
        )

        # =============================================
        # SUCCÈS
        # =============================================

        return Response(
            {
                "message": (
                    "Un lien de connexion vous a été "
                    "envoyé par e-mail."
                )
            },
            status=status.HTTP_200_OK
        )

class ConnexionParLienView(APIView):
    
    permission_classes = [AllowAny]

    def get(self, request, token):

        with transaction.atomic():

            try:
                lien = (
                    LienConnexion.objects
                    .select_for_update()
                    .select_related("utilisateur")
                    .get(token=token)
                )
                print(
    "DEBUG LIEN :",
    lien.id,
    lien.token,
    "utilise =",
    lien.utilise,
    "expiration =",
    lien.date_expiration,
)
            except LienConnexion.DoesNotExist:

                return Response(
                    {
                        "message": "Lien de connexion invalide."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # =============================================
            # LIEN DÉJÀ UTILISÉ
            # =============================================

            if lien.utilise:

                return Response(
                    {
                        "message": (
                            "Ce lien de connexion "
                            "a déjà été utilisé."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # =============================================
            # LIEN EXPIRÉ
            # =============================================

            if lien.date_expiration < timezone.now():

                return Response(
                    {
                        "message": (
                            "Ce lien de connexion "
                            "a expiré."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            utilisateur = lien.utilisateur

            # =============================================
            # COMPTE ACTIF
            # =============================================

            if not utilisateur.is_active:

                return Response(
                    {
                        "message": "Ce compte est désactivé."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # =============================================
            # CONSOMMER LE LIEN
            # =============================================

            lien.utilise = True

            lien.save(
                update_fields=["utilise"]
            )

            # =============================================
            # JWT
            # =============================================

            refresh = RefreshToken.for_user(
                utilisateur
            )

        return Response(
            {
                "message": "Connexion réussie.",

                "access": str(
                    refresh.access_token
                ),

                "refresh": str(
                    refresh
                ),

                "utilisateur": {
                    "id": utilisateur.id,
                    "prenom": utilisateur.prenom,
                    "nom": utilisateur.nom,
                    "email": utilisateur.email,
                    "role": utilisateur.role,
                }
            },
            status=status.HTTP_200_OK
        )

class VerificationEmailView(APIView):
    
    permission_classes = [AllowAny]

    def get(self, request, token):

        with transaction.atomic():

            try:
                verification = (
                    VerificationEmail.objects
                    .select_for_update()
                    .select_related("utilisateur")
                    .get(token=token)
                )

            except VerificationEmail.DoesNotExist:

                return Response(
                    {
                        "message": "Lien de vérification invalide."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # =============================================
            # TOKEN DÉJÀ UTILISÉ
            # =============================================

            if verification.utilise:

                return Response(
                    {
                        "message": (
                            "Ce lien de vérification "
                            "a déjà été utilisé."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # =============================================
            # TOKEN EXPIRÉ
            # =============================================

            if verification.date_expiration < timezone.now():

                return Response(
                    {
                        "message": (
                            "Ce lien de vérification "
                            "a expiré."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            utilisateur = verification.utilisateur

            # =============================================
            # VALIDATION DE L'EMAIL
            # =============================================

            utilisateur.email_verifie = True

            utilisateur.save(
                update_fields=["email_verifie"]
            )

            # =============================================
            # TOKEN CONSOMMÉ
            # =============================================

            verification.utilise = True

            verification.save(
                update_fields=["utilise"]
            )

            # =============================================
            # GÉNÉRATION DES JWT
            # =============================================

            refresh = RefreshToken.for_user(
                utilisateur
            )

        # =============================================
        # RÉPONSE
        # =============================================

        return Response(
            {
                "message": (
                    "Adresse e-mail vérifiée "
                    "avec succès."
                ),

                "access": str(
                    refresh.access_token
                ),

                "refresh": str(
                    refresh
                ),

                "utilisateur": {
                    "id": utilisateur.id,
                    "prenom": utilisateur.prenom,
                    "nom": utilisateur.nom,
                    "email": utilisateur.email,
                    "role": utilisateur.role,
                }
            },
            status=status.HTTP_200_OK
        )
        
        
        
