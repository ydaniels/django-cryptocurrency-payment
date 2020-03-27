=====
Usage
=====

To use Django Cryptocurrency Payment in a project, add it to your `INSTALLED_APPS` and configure cryptocurrency backend:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'cryptocurrency_payment.apps.CryptocurrencyPaymentConfig',
        ...
    )

    CRYPTOCURRENCY_PAYMENT = {
        "BITCOIN": {
            "CODE": "btc",
            "BACKEND": "merchant_wallet.backends.btc.BitcoinBackend",
            "FEE": 0.00,
            "REFRESH_PRICE_AFTER_MINUTE": 15,
            "REUSE_ADDRESS": False,
            "ACTIVE": True,
            "MASTER_PUBLIC_KEY": 'PUT_YOUR_WALLET_MASTER_PUBLIC_KEY',
            "CANCEL_UNPAID_PAYMENT_HRS": 24,
            "CREATE_NEW_UNDERPAID_PAYMENT": True,
            "IGNORE_UNDERPAYMENT_AMOUNT": 10,
            "IGNORE_CONFIRMED_BALANCE_WITHOUT_SAVED_HASH_MINS": 20,
            "BALANCE_CONFIRMATION_NUM": 1,
            "ALLOW_ANONYMOUS_PAYMENT": True,
        }
     }

Add Django Cryptocurrency Payment's URL patterns if you want the default payment view:

.. code-block:: python

    from cryptocurrency_payment import urls as cryptocurrency_payment_urls


    urlpatterns = [
        ...
        url(r'^', include(cryptocurrency_payment_urls)),
        ...
    ]


Create periodic task for these functions

.. code-block:: python


    cryptocurrency_payment.tasks.cancel_unpaid_payment
    cryptocurrency_payment.tasks.refresh_payment_prices
    cryptocurrency_payment.tasks.update_payment_status

To create a payment in you app

.. code-block:: python

    from cryptocurrency_payment.models import create_new_payment

    payment = create_new_payment(
    crypto='BITCOIN', #Cryptocurrency from your backend settings
    fiat_amount=10, #Amount of actual item in fiat
    fiat_currency='USD', #Fiat currency used to convert to crypto amount
    payment_title=None,  #Title associated with payment
    payment_description=None, #Description associated with payment
    related_object=None, #Generic linked object for this payment -> crypto_payments = GenericRelation(CryptoCurrencyPayment)
    user=None, #User of this payment for non-anonymous payment
    parent_payment=None, #Obvious
    address_index=None,# Use a particular address index for this payment
    reuse_address=None), #Used previously paid address for this payment

Or create child payment

.. code-block:: python

    from cryptocurrency_payment.models import create_new_payment
    child_payment = create_child_payment(payment, #Parent payment to attach this payment
     fiat_amount, #New amount for this payment based on parent payment currency
     )
Finally you can view payment at http://DJANO_HOST/APP/payment/PAYMENT.ID or use your own views or drf views for Cryptocurrencypayment model
