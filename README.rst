=============================
Django Cryptocurrency Payment
=============================

.. image:: https://badge.fury.io/py/django-cryptocurrency-payment.svg
    :target: https://badge.fury.io/py/django-cryptocurrency-payment

.. image:: https://travis-ci.org/ydaniels/django-cryptocurrency-payment.svg?branch=master
    :target: https://travis-ci.org/ydaniels/django-cryptocurrency-payment

.. image:: https://codecov.io/gh/ydaniels/django-cryptocurrency-payment/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/ydaniels/django-cryptocurrency-payment

.. image:: https://img.shields.io/badge/python-2.7%7C3.5%7C3.6%7C3.7%7C3.8-blue
   :alt: PyPI - Python Version
.. image:: https://img.shields.io/badge/django-1.11%7C2.0%7C2.1%7C2.2%7C3.0-blue
   :alt: Django Version

Simple and flexible pluggable cryptocurrency payment app for django

Documentation
-------------

The full documentation is at https://django-cryptocurrency-payment.readthedocs.io.

Quickstart
----------

Install Django Cryptocurrency Payment::

    pip install django-cryptocurrency-payment

Add it to your `INSTALLED_APPS`:

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

Add Django Cryptocurrency Payment's URL patterns:

.. code-block:: python

    from cryptocurrency_payment import urls as cryptocurrency_payment_urls


    urlpatterns = [
        ...
        url(r'^', include(cryptocurrency_payment_urls)), #/payment/{pk}/
        ...
    ]


Create payment with method

.. code-block:: python

    from cryptocurrency_payment.models import create_new_payment

    payment = create_new_payment(
    crypto='BITCOIN', #Cryptocurrency from your settings
    fiat_amount=10, #Amount of item in fiat
    fiat_currency='USD', #Fiat currency used to convert to crypto amount
    payment_title=None,  #Title associated with payment
    payment_description=None, #Description associated with payment
    related_object=None, #Generic linked object for this payment -> crypto_payments = GenericRelation(CryptoCurrencyPayment)
    user=None, #User of this payment for non-anonymous payment
    parent_payment=None, #uhh duh
    address_index=None,# Use a particular address index for this payment
    reuse_address=None), #Used previously paid address for this payment


Features
--------

* Flexible payment creation that can be linked to other django object
* Automatically update payment status from blockchain
* Auto update payment prices if payment is not paid
* Auto create child payment if payment is underpaid
* Cancel unpaid payment after a period of time
* Allow Anonymous payment
* Pluggable backend to support more cryptocurrency


Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox

Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
