from django.db import models


class Paiement(models.Model):

    TYPE_CHOICES = [
        ("ABONNEMENT", "Abonnement"),
        ("COMMANDE", "Commande"),
    ]

    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente"),
        ("PAYE", "Payé"),
        ("ECHEC", "Échec"),
        ("ANNULE", "Annulé"),
    ]

    MOYEN_CHOICES = [
        ("WAVE", "Wave"),
        ("ORANGE_MONEY", "Orange Money"),
        ("FREE_MONEY", "Free Money"),
        ("EXPRESSO", "Expresso"),
        ("CARTE", "Carte bancaire"),
    ]

    utilisateur = models.ForeignKey(
        "utilisateurs.Utilisateur",
        on_delete=models.CASCADE,
        related_name="paiements"
    )

    abonnement = models.ForeignKey(
        "abonnements.AbonnementAgronome",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paiements"
    )

    type_paiement = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES
    )

    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    moyen_paiement = models.CharField(
        max_length=30,
        choices=MOYEN_CHOICES,
        null=True,
        blank=True
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="EN_ATTENTE"
    )

    reference = models.CharField(
        max_length=150,
        unique=True
    )

    token_paydunya = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    url_paiement = models.URLField(
        blank=True,
        null=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    date_paiement = models.DateTimeField(
        null=True,
        blank=True
    )

    date_modification = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.reference} - {self.montant} FCFA"