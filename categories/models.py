from django.db import models
class Categorie(models.Model):
    nom = models.CharField(
        max_length=100,
        unique=True)

    description = models.TextField(
        blank=True
    )

    active = models.BooleanField(
        default=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class UniteVente(models.Model):
    nom = models.CharField(
        max_length=100,
        unique=True
    )

    symbole = models.CharField(
        max_length=20,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    active = models.BooleanField(
        default=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Unité de vente"
        verbose_name_plural = "Unités de vente"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.symbole})"
class MoyenPaiement(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Moyen de paiement"
        verbose_name_plural = "Moyens de paiement"
        ordering = ["nom"]

    def __str__(self):
        return self.nom