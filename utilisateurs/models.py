
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UtilisateurManager(BaseUserManager):

    def create_user(self, email, nom, prenom, telephone, role="AGRONOME"):
        if not email:
            raise ValueError("L'adresse email est obligatoire")

        user = self.model(
            email=self.normalize_email(email),
            nom=nom,
            prenom=prenom,
            telephone=telephone,
            role="AGRONOME",
            is_staff=False,
            is_superuser=False,
            is_active=True,
        )

        user.set_unusable_password()
        user.save(using=self._db)

        return user

    def create_superuser(self, email, nom, prenom, telephone, password):
        user = self.model(
            email=self.normalize_email(email),
            nom=nom,
            prenom=prenom,
            telephone=telephone,
            role="ADMIN",
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user


class Utilisateur(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = [
        ("AGRONOME", "Agronome"),
        ("ADMIN", "Administrateur"),
    ]

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    telephone = models.CharField(max_length=20)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="AGRONOME"
    )

    photo = models.ImageField(
        upload_to="agronomes/",
        blank=True,
        null=True
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    email_verifie = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UtilisateurManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = [
        "nom",
        "prenom",
        "telephone",
    ]

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class VerificationEmail(models.Model):
    
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="verification_email"
    )

    token = models.CharField(
        max_length=255,
        unique=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    date_expiration = models.DateTimeField()

    utilise = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"Vérification email - {self.utilisateur.email}"
    
    
class LienConnexion(models.Model):
    
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="liens_connexion"
    )

    token = models.CharField(
        max_length=255,
        unique=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    date_expiration = models.DateTimeField()

    utilise = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"Lien connexion - {self.utilisateur.email}"    



class CompteReversement(models.Model):
    utilisateur = models.OneToOneField(
        "utilisateurs.Utilisateur",
        on_delete=models.CASCADE,
        related_name="compte_reversement",
    )

    account_alias = models.CharField(
        max_length=255,
        unique=True,
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

    def __str__(self):
        return (
            f"{self.utilisateur} - "
            f"{self.account_alias}"
        )