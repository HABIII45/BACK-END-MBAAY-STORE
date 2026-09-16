
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
            role=role,
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