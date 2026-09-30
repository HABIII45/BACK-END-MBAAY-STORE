import paydunya

from django.conf import settings
from django.utils import timezone
from decimal import Decimal

from paydunya import InvoiceItem, Store


# ==========================================================
# CONFIGURATION PAYDUNYA
# ==========================================================

def configurer_paydunya():
    """
    Configure les clés API et le mode PayDunya.
    """

    paydunya.api_keys = {
        "PAYDUNYA-MASTER-KEY": settings.PAYDUNYA_MASTER_KEY,
        "PAYDUNYA-PRIVATE-KEY": settings.PAYDUNYA_PRIVATE_KEY,
        "PAYDUNYA-TOKEN": settings.PAYDUNYA_TOKEN,
    }

    paydunya.debug = settings.PAYDUNYA_MODE == "test"


# ==========================================================
# EXTRACTION DE LA REPONSE PAYDUNYA
# ==========================================================

def extraire_resultat_facture(response):
    """
    Extrait le token et l'URL de paiement de la réponse
    retournée par PayDunya.
    """

    token = None
    url_paiement = None

    # ------------------------------------------------------
    # Cas où la réponse est un dictionnaire
    # ------------------------------------------------------

    if isinstance(response, dict):

        # Réponse directe :
        # {
        #     "token": "...",
        #     "response_text": "https://..."
        # }

        token = response.get("token")

        url_paiement = (
            response.get("response_text")
            or response.get("url")
            or response.get("response_url")
        )

        # --------------------------------------------------
        # Certains formats peuvent contenir "data"
        # --------------------------------------------------

        if not token and isinstance(response.get("data"), dict):

            data = response["data"]

            token = data.get("token")

            url_paiement = (
                data.get("response_text")
                or data.get("url")
                or data.get("response_url")
            )

            # ------------------------------------------------
            # Certains retours peuvent contenir "invoice"
            # ------------------------------------------------

            invoice_data = data.get("invoice")

            if isinstance(invoice_data, dict):

                if not token:
                    token = invoice_data.get("token")

                if not url_paiement:
                    url_paiement = (
                        invoice_data.get("response_text")
                        or invoice_data.get("url")
                    )

        # --------------------------------------------------
        # Format éventuel :
        # {
        #     "invoice": {
        #         "token": "..."
        #     }
        # }
        # --------------------------------------------------

        if not token and isinstance(
            response.get("invoice"),
            dict
        ):

            invoice_data = response["invoice"]

            token = invoice_data.get("token")

            if not url_paiement:
                url_paiement = (
                    invoice_data.get("response_text")
                    or invoice_data.get("url")
                )

    return token, url_paiement


# ==========================================================
# FACTURE COMMANDE
# ==========================================================

def creer_facture_commande(
    paiement,
    commandes,
):
    """
    Crée une facture PayDunya pour une ou plusieurs commandes.
    """

    configurer_paydunya()

    # ------------------------------------------------------
    # Boutique PayDunya
    # ------------------------------------------------------

    store = Store(
        name=settings.PAYDUNYA_STORE_NAME
    )

    facture = paydunya.Invoice(store)

    total = Decimal("0.00")

    # ------------------------------------------------------
    # Parcourir les commandes
    # ------------------------------------------------------

    for commande in commandes:

        # --------------------------------------------------
        # Produits
        # --------------------------------------------------

        for ligne in commande.lignes.all():

            total += ligne.total

            facture.add_item(
                InvoiceItem(
                    name=ligne.produit.nom,
                    quantity=float(ligne.quantite),
                    unit_price=str(ligne.prix_unitaire),
                    total_price=str(ligne.total),
                    description=(
                        f"{commande.boutique.nom} "
                        f"- {ligne.produit.nom}"
                    ),
                )
            )

        # --------------------------------------------------
        # Frais de livraison
        # --------------------------------------------------

        if commande.frais_livraison > Decimal("0.00"):

            total += commande.frais_livraison

            facture.add_item(
                InvoiceItem(
                    name="Frais de livraison",
                    quantity=1,
                    unit_price=str(
                        commande.frais_livraison
                    ),
                    total_price=str(
                        commande.frais_livraison
                    ),
                    description=(
                        f"Livraison - "
                        f"{commande.boutique.nom}"
                    ),
                )
            )

    # ------------------------------------------------------
    # Vérification du montant
    # ------------------------------------------------------

    if total != paiement.montant:

        return {
            "success": False,
            "message": (
                "Le montant de la facture ne correspond "
                "pas au montant du paiement."
            ),
        }

    # ------------------------------------------------------
    # Montant total
    # ------------------------------------------------------

    facture.total_amount = int(total)

    facture.description = (
        f"Commande(s) MBAAY STORE - "
        f"{paiement.reference}"
    )

    # ------------------------------------------------------
    # Données personnalisées
    # ------------------------------------------------------

    facture.add_custom_data([
        (
            "reference_mbaay",
            paiement.reference,
        ),
        (
            "paiement_id",
            paiement.id,
        ),
        (
            "type_paiement",
            "COMMANDE",
        ),
    ])

    # ------------------------------------------------------
    # URLs
    # ------------------------------------------------------

    facture.callback_url = (
        settings.PAYDUNYA_IPN_URL
    )

    facture.return_url = (
        settings.PAYDUNYA_RETURN_URL
    )

    facture.cancel_url = (
        settings.PAYDUNYA_CANCEL_URL
    )

    # ------------------------------------------------------
    # Création de la facture
    # ------------------------------------------------------

    successful, response = facture.create()

    if not successful:

        return {
            "success": False,
            "message": str(response),
        }

    # ------------------------------------------------------
    # Extraction du token et de l'URL
    # ------------------------------------------------------

    token, url_paiement = (
        extraire_resultat_facture(response)
    )

    # ------------------------------------------------------
    # Vérification
    # ------------------------------------------------------

    if not token:

        return {
            "success": False,
            "message": (
                "PayDunya a créé la facture mais aucun "
                "token de paiement n'a été trouvé."
            ),
        }

    if not url_paiement:

        return {
            "success": False,
            "message": (
                "PayDunya a créé la facture mais aucune "
                "URL de paiement n'a été trouvée."
            ),
        }

    # ------------------------------------------------------
    # Enregistrer dans la base
    # ------------------------------------------------------

    paiement.token_paydunya = token
    paiement.url_paiement = url_paiement

    paiement.save(
        update_fields=[
            "token_paydunya",
            "url_paiement",
            "date_modification",
        ]
    )

    return {
        "success": True,
        "token": token,
        "url_paiement": url_paiement,
    }


# ==========================================================
# REVERSEMENT
# ==========================================================

def effectuer_reversement(reversement):
    """
    Effectue le reversement du montant de la commande
    vers le compte PayDunya de l'agronome.
    """

    configurer_paydunya()

    compte = reversement.compte_reversement

    if not compte.actif:

        return {
            "success": False,
            "message": (
                "Le compte de reversement est désactivé."
            ),
        }

    montant = int(reversement.montant)

    if montant <= 0:

        return {
            "success": False,
            "message": (
                "Le montant du reversement est invalide."
            ),
        }

    try:

        direct_pay = paydunya.DirectPay(
            compte.account_alias,
            montant,
        )

        successful, response = (
            direct_pay.process()
        )

        if successful:

            reversement.statut = "VERSE"
            reversement.date_execution = (
                timezone.now()
            )

            reversement.save(
                update_fields=[
                    "statut",
                    "date_execution",
                    "date_modification",
                ]
            )

            return {
                "success": True,
                "message": (
                    "Reversement effectué avec succès."
                ),
                "transaction_id": (
                    response.get("transaction_id")
                    if isinstance(response, dict)
                    else None
                ),
            }

        reversement.statut = "ECHEC"

        reversement.save(
            update_fields=[
                "statut",
                "date_modification",
            ]
        )

        return {
            "success": False,
            "message": str(response),
        }

    except Exception as e:

        reversement.statut = "ECHEC"

        reversement.save(
            update_fields=[
                "statut",
                "date_modification",
            ]
        )

        return {
            "success": False,
            "message": str(e),
        }


# ==========================================================
# FACTURE ABONNEMENT
# ==========================================================

def creer_facture_abonnement(
    paiement,
    abonnement,
):
    """
    Crée une facture PayDunya pour un abonnement
    MBAAY STORE.
    """

    configurer_paydunya()

    # ------------------------------------------------------
    # Boutique PayDunya
    # ------------------------------------------------------

    store = Store(
        name=settings.PAYDUNYA_STORE_NAME
    )

    facture = paydunya.Invoice(store)

    # ------------------------------------------------------
    # Déterminer le libellé
    # ------------------------------------------------------

    if abonnement.type_abonnement == "MENSUEL":

        nom = (
            "Abonnement MBAAY STORE - Mensuel"
        )

    else:

        nom = (
            "Abonnement MBAAY STORE - Annuel"
        )

    # ------------------------------------------------------
    # Ajouter l'abonnement
    # ------------------------------------------------------

    facture.add_item(
        InvoiceItem(
            name=nom,
            quantity=1,
            unit_price=str(
                paiement.montant
            ),
            total_price=str(
                paiement.montant
            ),
            description=(
                f"Abonnement "
                f"{abonnement.type_abonnement} "
                f"- MBAAY STORE"
            ),
        )
    )

    # ------------------------------------------------------
    # Montant
    # ------------------------------------------------------

    facture.total_amount = int(
        paiement.montant
    )

    facture.description = (
        f"Abonnement MBAAY STORE - "
        f"{paiement.reference}"
    )

    # ------------------------------------------------------
    # Données personnalisées
    # ------------------------------------------------------

    facture.add_custom_data([
        (
            "reference_mbaay",
            paiement.reference,
        ),
        (
            "paiement_id",
            paiement.id,
        ),
        (
            "type_paiement",
            "ABONNEMENT",
        ),
        (
            "abonnement_id",
            abonnement.id,
        ),
    ])

    # ------------------------------------------------------
    # URLs PayDunya
    # ------------------------------------------------------

    facture.callback_url = (
        settings.PAYDUNYA_IPN_URL
    )

    facture.return_url = (
        settings.PAYDUNYA_RETURN_URL
    )

    facture.cancel_url = (
        settings.PAYDUNYA_CANCEL_URL
    )

    # ------------------------------------------------------
    # Création de la facture
    # ------------------------------------------------------

    successful, response = facture.create()

    if not successful:

        return {
            "success": False,
            "message": str(response),
        }

    # ------------------------------------------------------
    # Extraction du token et de l'URL
    # ------------------------------------------------------

    token, url_paiement = (
        extraire_resultat_facture(response)
    )

    # ------------------------------------------------------
    # Vérification
    # ------------------------------------------------------

    if not token:

        return {
            "success": False,
            "message": (
                "PayDunya a créé la facture mais aucun "
                "token de paiement n'a été trouvé."
            ),
        }

    if not url_paiement:

        return {
            "success": False,
            "message": (
                "PayDunya a créé la facture mais aucune "
                "URL de paiement n'a été trouvée."
            ),
        }

    # ------------------------------------------------------
    # Enregistrer dans la base
    # ------------------------------------------------------

    paiement.token_paydunya = token
    paiement.url_paiement = url_paiement

    paiement.save(
        update_fields=[
            "token_paydunya",
            "url_paiement",
            "date_modification",
        ]
    )

    return {
        "success": True,
        "token": token,
        "url_paiement": url_paiement,
    }