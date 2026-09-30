from django.db import models


class InformationAgricole(models.Model):

    CATEGORIE_CHOICES = [
        ("OPPORTUNITE", "Opportunité"),
        ("ACTUALITE", "Actualité"),
        ("EVENEMENT", "Événement"),
        ("FORMATION", "Formation"),
    ]

    titre = models.CharField(max_length=255)

    description = models.TextField()

    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIE_CHOICES
    )

    source = models.CharField(max_length=255)

    url = models.URLField(max_length=500 ,unique=True )

    date_publication = models.DateTimeField()

    date_evenement = models.DateTimeField(
        null=True,
        blank=True
    )

    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-date_publication"]
        verbose_name = "Information agricole"
        verbose_name_plural = "Informations agricoles"

    def __str__(self):
        return self.titre