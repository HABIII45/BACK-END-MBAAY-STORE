from django.db import transaction
from django.utils.text import slugify

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Boutique
from .serializers import BoutiqueSerializer, CreationEspaceSerializer
from utilisateurs.models import Utilisateur


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

    def get_serializer_class(self):

        if self.action == "creation_espace":
            return CreationEspaceSerializer

        return BoutiqueSerializer

    @action(
        detail=False,
        methods=["post"],
        url_path="creation-espace"
    )
    def creation_espace(self, request):

        # 1. Validation des données reçues
        serializer = CreationEspaceSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        # 2. Création du compte + boutique dans une seule transaction
        with transaction.atomic():

            # Création du compte agronome
            utilisateur = Utilisateur.objects.create_user(
                email=data["email"],
                nom=data["nom"],
                prenom=data["prenom"],
                telephone=data["telephone"],
                role="AGRONOME"
            )

            # Création de la boutique
            boutique = Boutique.objects.create(
                proprietaire=utilisateur,
                nom=data["nom_boutique"],
                slug=generer_slug_unique(
                    data["nom_boutique"]
                ),
                description=data["description_boutique"],
                latitude=data["latitude"],
                longitude=data["longitude"]
            )

        # 3. Réponse envoyée au frontend
        return Response(
            {
                "message": "Votre espace a été créé avec succès.",

                "utilisateur": {
                    "id": utilisateur.id,
                    "prenom": utilisateur.prenom,
                    "nom": utilisateur.nom,
                    "email": utilisateur.email,
                    "telephone": utilisateur.telephone,
                },

                "boutique": BoutiqueSerializer(boutique).data
            },
            status=status.HTTP_201_CREATED
        )