import secrets

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Commande(models.Model):

    STATUT_CHOICES = [
        ("EN_ATTENTE_PAIEMENT", "En attente de paiement"),
        ("PAYEE", "Payée"),
        ("EN_PREPARATION", "En préparation"),
        ("PRETE", "Prête"),
        ("EN_LIVRAISON", "En livraison"),
        ("LIVREE", "Livrée"),
        ("PROBLEME", "Problème signalé"),
        ("ANNULEE", "Annulée"),
    ]

    boutique = models.ForeignKey(
        "boutiques.Boutique",
        on_delete=models.PROTECT,
        related_name="commandes"
    )

    mode_livraison = models.ForeignKey(
        "livraisons.ModeLivraison",
        on_delete=models.PROTECT,
        related_name="commandes"
    )

    reference = models.CharField(
        max_length=50,
        unique=True
    )

    token_suivi = models.CharField(
        max_length=128,
        unique=True,
        db_index=True
    )

    code_reception = models.CharField(
        max_length=20
    )

    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default="EN_ATTENTE_PAIEMENT"
    )

    sous_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    frais_livraison = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    date_paiement = models.DateTimeField(
        null=True,
        blank=True
    )

    date_livraison = models.DateTimeField(
        null=True,
        blank=True
    )

    date_modification = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.reference} - {self.boutique.nom}"

    def generer_token_suivi(self):
        return secrets.token_urlsafe(32)

    def generer_code_reception(self):
        return str(secrets.randbelow(900000) + 100000)


class LigneCommande(models.Model):

    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        related_name="lignes"
    )

    produit = models.ForeignKey(
        "produits.Produit",
        on_delete=models.PROTECT,
        related_name="lignes_commandes"
    )

    quantite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01"))
        ]
    )

    prix_unitaire = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    class Meta:
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"

    def __str__(self):
        return f"{self.produit.nom} x {self.quantite}"