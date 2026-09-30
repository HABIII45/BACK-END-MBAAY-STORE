from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator

class ModeLivraison(models.Model):
    """
    Modes de livraison autorisés par MBAAY.
    L'admin active ou désactive les modes disponibles
    pour les agronomes.
    """

    nom = models.CharField(
        max_length=100,
        unique=True
    )

    code = models.CharField(
        max_length=50,
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
        verbose_name = "Mode de livraison"
        verbose_name_plural = "Modes de livraison"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class ParametreLivraison(models.Model):
    """
    Paramètres globaux de la plateforme MBAAY.

    Ces paramètres ne définissent pas les règles propres
    à chaque agronome.
    """

    regroupement_automatique = models.BooleanField(
        default=True
    )

    active = models.BooleanField(
        default=True
    )

    date_modification = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Paramètre de livraison"
        verbose_name_plural = "Paramètres de livraison"

    def __str__(self):
        return "Paramètres de livraison MBAAY"


class ConfigurationLivraisonBoutique(models.Model):
    """
    Configuration de livraison propre à une boutique.

    L'agronome choisit ici les modes de livraison qu'il souhaite
    proposer parmi ceux autorisés par MBAAY.
    """
    TYPE_TARIFICATION_CHOICES = [
        ("FIXE", "Tarif fixe"),
        ("DISTANCE", "Tarif selon la distance"),
        ]
    boutique = models.OneToOneField(
        "boutiques.Boutique",
        on_delete=models.CASCADE,
        related_name="configuration_livraison"
    )
    

    modes_livraison = models.ManyToManyField(
        ModeLivraison,
        blank=True,
        related_name="configurations_boutiques"
    )
    type_tarification = models.CharField(
       max_length=20,
       choices=TYPE_TARIFICATION_CHOICES,
       default="FIXE"
    )

    frais_livraison_fixe = models.DecimalField(
       max_digits=10,
       decimal_places=2,
       default=Decimal("0.00"),
        validators=[
        MinValueValidator(Decimal("0.00"))
    ]
)
    nombre_max_commandes_par_livreur = models.PositiveIntegerField(
        default=5
    )

    regroupement_automatique = models.BooleanField(
        default=True
    )

    date_modification = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Configuration de livraison"
        verbose_name_plural = "Configurations de livraison"

    def __str__(self):
        return f"Livraison - {self.boutique}"


class ContactLivreur(models.Model):
    """
    Livreur utilisé par l'agronome.

    Ce livreur est externe à MBAAY :
    il n'a pas de compte utilisateur MBAAY.
    """

    boutique = models.ForeignKey(
        "boutiques.Boutique",
        on_delete=models.CASCADE,
        related_name="contacts_livreurs"
    )

    nom = models.CharField(
        max_length=150
    )

    telephone = models.CharField(
        max_length=30
    )

    actif = models.BooleanField(
        default=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Contact livreur"
        verbose_name_plural = "Contacts livreurs"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} - {self.telephone}"
    
class TarifLivraisonDistance(models.Model):
    configuration = models.ForeignKey(
        ConfigurationLivraisonBoutique,
        on_delete=models.CASCADE,
        related_name="tarifs_distance"
    )

    distance_min_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    distance_max_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    class Meta:
        ordering = ["distance_min_km"]

    def __str__(self):
        return (
            f"{self.distance_min_km} - "
            f"{self.distance_max_km} km : "
            f"{self.montant} FCFA"
        )