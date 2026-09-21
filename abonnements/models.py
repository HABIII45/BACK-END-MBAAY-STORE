
from django.db import models

class Abonnement(models.Model):
    """
    Configuration générale de l'offre d'abonnement MBAAY.

    L'Admin configure ici les tarifs et décide si l'option
    d'essai gratuit est actuellement proposée.
    """

    prix_mensuel = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    prix_annuel = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    essai_gratuit_actif = models.BooleanField(
        default=True
    )

    duree_essai_jours = models.PositiveIntegerField(
        default=30
    )

    actif = models.BooleanField(
        default=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    date_modification = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Configuration abonnement"
        verbose_name_plural = "Configuration abonnement"

    def __str__(self):
        return "Configuration abonnement MBAAY"


class AbonnementAgronome(models.Model):

    TYPE_CHOICES = [
        ("ESSAI", "Essai gratuit"),
        ("MENSUEL", "Abonnement mensuel"),
        ("ANNUEL", "Abonnement annuel"),
    ]

    STATUT_CHOICES = [
        ("ACTIF", "Actif"),
        ("EXPIRE", "Expiré"),
        ("SUSPENDU", "Suspendu"),
    ]

    STATUT_PAIEMENT_CHOICES = [
        ("NON_REQUIS", "Non requis"),
        ("EN_ATTENTE", "En attente"),
        ("PAYE", "Payé"),
        ("ECHEC", "Échec"),
    ]

    agronome = models.ForeignKey(
        "utilisateurs.Utilisateur",
        on_delete=models.CASCADE,
        related_name="abonnements"
    )

    type_abonnement = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    date_debut = models.DateTimeField()

    date_fin = models.DateTimeField()

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="ACTIF"
    )

    statut_paiement = models.CharField(
        max_length=20,
        choices=STATUT_PAIEMENT_CHOICES,
        default="NON_REQUIS"
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    date_modification = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Abonnement agronome"
        verbose_name_plural = "Abonnements agronomes"
        ordering = ["-date_creation"]

    def __str__(self):
        return (
            f"{self.agronome} - "
            f"{self.get_type_abonnement_display()}"
        )

