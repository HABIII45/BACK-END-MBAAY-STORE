
import uuid

from django.core.validators import MinValueValidator
from django.db import models

from produits.models import Produit


class Panier(models.Model):

    identifiant = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    date_modification = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Panier {self.identifiant}"


class LignePanier(models.Model):

    panier = models.ForeignKey(
        Panier,
        on_delete=models.CASCADE,
        related_name="lignes"
    )

    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name="lignes_panier"
    )

    quantite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0.01)
        ]
    )

    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0)
        ]
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    date_modification = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.produit.nom} "
            f"x {self.quantite}"
        )

