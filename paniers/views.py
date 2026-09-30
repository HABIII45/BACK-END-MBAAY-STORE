from decimal import Decimal

from django.shortcuts import get_object_or_404

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from produits.models import Produit

from .models import Panier, LignePanier
from .serializers import PanierSerializer, LignePanierSerializer


def recuperer_panier(request):
    """
    Récupère le panier du visiteur grâce à son identifiant.
    Si aucun identifiant n'est fourni, un nouveau panier est créé.
    """

    panier_id = request.headers.get("X-Panier-ID")

    if panier_id:
        try:
            panier = Panier.objects.get(
                identifiant=panier_id
            )
            return panier, False

        except (Panier.DoesNotExist, ValueError):
            pass

    panier = Panier.objects.create()

    return panier, True


class PanierView(APIView):
    """
    Récupérer le panier actuel.
    """

    permission_classes = [AllowAny]

    def get(self, request):

        panier, nouveau = recuperer_panier(request)

        panier = (
            Panier.objects
            .prefetch_related(
                "lignes__produit__boutique",
                "lignes__produit__unite_vente",
            )
            .get(pk=panier.pk)
        )

        serializer = PanierSerializer(panier)

        return Response({
            "success": True,
            "nouveau_panier": nouveau,
            "panier": serializer.data,
        })


class AjouterAuPanierView(APIView):
    """
    Ajouter un produit au panier.
    """

    permission_classes = [AllowAny]

    def post(self, request):

        panier, nouveau = recuperer_panier(request)

        produit_id = request.data.get("produit")
        quantite = request.data.get("quantite", 1)

        if not produit_id:
            return Response(
                {
                    "success": False,
                    "message": "Le produit est obligatoire.",
                },
                status=400,
            )

        try:
            quantite = Decimal(str(quantite))
        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "La quantité est invalide.",
                },
                status=400,
            )

        if quantite <= 0:
            return Response(
                {
                    "success": False,
                    "message": "La quantité doit être supérieure à zéro.",
                },
                status=400,
            )

        produit = get_object_or_404(
            Produit.objects.select_related(
                "boutique",
                "unite_vente",
            ),
            id=produit_id,
            disponible=True,
            boutique__statut="PUBLIEE",
        )

        if produit.stock_actuel <= 0:
            return Response(
                {
                    "success": False,
                    "message": "Ce produit n'est plus disponible.",
                },
                status=400,
            )

        ligne = (
            LignePanier.objects
            .filter(
                panier=panier,
                produit=produit,
            )
            .first()
        )

        if ligne:
            nouvelle_quantite = ligne.quantite + quantite

            if nouvelle_quantite > produit.stock_actuel:
                return Response(
                    {
                        "success": False,
                        "message": (
                            "La quantité demandée dépasse "
                            "le stock disponible."
                        ),
                    },
                    status=400,
                )

            ligne.quantite = nouvelle_quantite
            ligne.save(
                update_fields=[
                    "quantite",
                    "date_modification",
                ]
            )

        else:

            if quantite > produit.stock_actuel:
                return Response(
                    {
                        "success": False,
                        "message": (
                            "La quantité demandée dépasse "
                            "le stock disponible."
                        ),
                    },
                    status=400,
                )

            ligne = LignePanier.objects.create(
                panier=panier,
                produit=produit,
                quantite=quantite,
                prix_unitaire=produit.prix,
            )

        serializer = LignePanierSerializer(ligne)

        return Response(
            {
                "success": True,
                "nouveau_panier": nouveau,
                "message": "Produit ajouté au panier.",
                "ligne": serializer.data,
                "panier_id": str(panier.identifiant),
            },
            status=201,
        )


class ModifierQuantitePanierView(APIView):
    """
    Modifier la quantité d'une ligne du panier.
    """

    permission_classes = [AllowAny]

    def patch(self, request, ligne_id):

        panier_id = request.headers.get("X-Panier-ID")

        if not panier_id:
            return Response(
                {
                    "success": False,
                    "message": "Identifiant du panier manquant.",
                },
                status=400,
            )

        try:
            panier = Panier.objects.get(
                identifiant=panier_id
            )
        except (Panier.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Panier introuvable.",
                },
                status=404,
            )

        ligne = get_object_or_404(
            LignePanier.objects.select_related("produit"),
            id=ligne_id,
            panier=panier,
        )

        quantite = request.data.get("quantite")

        if quantite is None:
            return Response(
                {
                    "success": False,
                    "message": "La quantité est obligatoire.",
                },
                status=400,
            )

        try:
            quantite = Decimal(str(quantite))
        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "La quantité est invalide.",
                },
                status=400,
            )

        if quantite <= 0:
            return Response(
                {
                    "success": False,
                    "message": "La quantité doit être supérieure à zéro.",
                },
                status=400,
            )

        if quantite > ligne.produit.stock_actuel:
            return Response(
                {
                    "success": False,
                    "message": "La quantité dépasse le stock disponible.",
                },
                status=400,
            )

        ligne.quantite = quantite
        ligne.save(
            update_fields=[
                "quantite",
                "date_modification",
            ]
        )

        serializer = LignePanierSerializer(ligne)

        return Response({
            "success": True,
            "message": "Quantité mise à jour.",
            "ligne": serializer.data,
        })


class SupprimerLignePanierView(APIView):
    """
    Supprimer un produit du panier.
    """

    permission_classes = [AllowAny]

    def delete(self, request, ligne_id):

        panier_id = request.headers.get("X-Panier-ID")

        if not panier_id:
            return Response(
                {
                    "success": False,
                    "message": "Identifiant du panier manquant.",
                },
                status=400,
            )

        try:
            panier = Panier.objects.get(
                identifiant=panier_id
            )
        except (Panier.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Panier introuvable.",
                },
                status=404,
            )

        ligne = get_object_or_404(
            LignePanier,
            id=ligne_id,
            panier=panier,
        )

        ligne.delete()

        return Response({
            "success": True,
            "message": "Produit retiré du panier.",
        })


class ViderPanierView(APIView):
    """
    Supprimer toutes les lignes du panier.
    """

    permission_classes = [AllowAny]

    def delete(self, request):

        panier_id = request.headers.get("X-Panier-ID")

        if not panier_id:
            return Response(
                {
                    "success": False,
                    "message": "Identifiant du panier manquant.",
                },
                status=400,
            )

        try:
            panier = Panier.objects.get(
                identifiant=panier_id
            )
        except (Panier.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Panier introuvable.",
                },
                status=404,
            )

        panier.lignes.all().delete()

        return Response({
            "success": True,
            "message": "Panier vidé.",
        })