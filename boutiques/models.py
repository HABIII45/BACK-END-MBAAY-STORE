from django.db import models
from django.conf import settings


class Boutique(models.Model):

    STATUT_CHOICES = [
        ("BROUILLON", "Brouillon"),
        ("PUBLIEE", "Publiée"),
        ("SUSPENDUE", "Suspendue"),
    ]

    proprietaire = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="boutique"
    )

    nom = models.CharField(max_length=150)

    slug = models.SlugField(
        max_length=180,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    logo = models.ImageField(
        upload_to="boutiques/logos/",
        blank=True,
        null=True
    )

    image = models.ImageField(
        upload_to="boutiques/images/",
        blank=True,
        null=True
    )

    couleur_principale = models.CharField(
        max_length=20,
        blank=True
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="BROUILLON"
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    date_modification = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.nom