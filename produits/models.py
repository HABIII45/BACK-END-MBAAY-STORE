from django.core.validators import MinValueValidator
from django.db import models

from boutiques.models import Boutique
from categories.models import Categorie, UniteVente




class Produit(models.Model):
    boutique = models.ForeignKey(
        Boutique,
        on_delete=models.CASCADE,
        related_name="produits"
    )

    nom = models.CharField(max_length=150)

    description = models.TextField(blank=True)

    prix = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        related_name="produits"
    )

    unite_vente = models.ForeignKey(
        UniteVente,
        on_delete=models.PROTECT,
        related_name="produits"
    )

    # Quantité disponible au moment de la création du produit
    stock_initial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Quantité actuellement disponible à la vente
    stock_actuel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    # Quantité totale vendue depuis la création du produit
    quantite_vendue = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0,
    validators=[MinValueValidator(0)]
    )
    # Permet de désactiver manuellement la vente du produit
    disponible = models.BooleanField(default=True)

    image = models.ImageField(
        upload_to="produits/",
        blank=True,
        null=True
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.nom} - {self.boutique.nom}"