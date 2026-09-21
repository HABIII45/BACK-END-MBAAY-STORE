from django.db import models


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

    boutique = models.OneToOneField(
        "boutiques.Boutique",
        on_delete=models.CASCADE,
        related_name="configuration_livraison"
    )

    livraison_par_acheteur = models.BooleanField(
        default=False
    )

    livraison_par_agronome = models.BooleanField(
        default=False
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