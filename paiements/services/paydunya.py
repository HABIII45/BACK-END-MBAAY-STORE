import paydunya
from django.conf import settings


def configurer_paydunya():
    paydunya.api_keys = {
        "PAYDUNYA-MASTER-KEY": settings.PAYDUNYA_MASTER_KEY,
        "PAYDUNYA-PRIVATE-KEY": settings.PAYDUNYA_PRIVATE_KEY,
        "PAYDUNYA-TOKEN": settings.PAYDUNYA_TOKEN,
    }

    paydunya.debug = settings.PAYDUNYA_MODE == "test"


def creer_facture_abonnement(
    paiement,
    nom_client,
    email_client,
):
    configurer_paydunya()

    facture = paydunya.Invoice()

    facture.add_item(
        "Abonnement MBAAY STORE",
        1,
        str(paiement.montant),
        str(paiement.montant),
        "Abonnement SaaS MBAAY STORE",
    )

    facture.total_amount = int(paiement.montant)

    facture.description = (
        f"Abonnement MBAAY STORE - {paiement.reference}"
    )

    facture.add_custom_data([
        ("reference_mbaay", paiement.reference),
        ("paiement_id", paiement.id),
        ("abonnement_id", paiement.abonnement_id),
    ])

    facture.callback_url = settings.PAYDUNYA_IPN_URL
    facture.return_url = settings.PAYDUNYA_RETURN_URL
    facture.cancel_url = settings.PAYDUNYA_CANCEL_URL

    successful, response = facture.create()

    if successful:
        paiement.token_paydunya = facture.token
        paiement.url_paiement = facture.response_text

        paiement.save(
            update_fields=[
                "token_paydunya",
                "url_paiement",
                "date_modification",
            ]
        )

        return {
            "success": True,
            "token": facture.token,
            "url_paiement": facture.response_text,
        }

    return {
        "success": False,
        "message": str(response),
    }