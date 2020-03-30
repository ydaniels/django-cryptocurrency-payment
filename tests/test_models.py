#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-cryptocurrency-payment
------------

Tests for `django-cryptocurrency-payment` models module.
"""

from django.test import TestCase

from django.contrib.auth import get_user_model

from cryptocurrency_payment.models import (
    create_new_payment,
    create_child_payment,
    CryptoCurrencyPayment,
)
from cryptocurrency_payment.app_settings import get_backend_obj

# from merchant_wallet.backends.btc import BitcoinBackend
from cryptocurrency_payment.test_utils.test_app.models import Invoice


class TestCryptocurrencyModel(TestCase):
    def setUp(self):
        self.crypto = "Bitcoin"
        self.crypto_two = "Bitcointest"
        self.backend = get_backend_obj(self.crypto)

    def test_create_new_payment(self):

        fait_amount = 20
        fiat_currency = "USD"
        payment_title = "Buy Shirt"
        payment_description = "Buy One Get Free  "
        payment = create_new_payment(
            self.crypto,
            fiat_amount=fait_amount,
            fiat_currency=fiat_currency,
            payment_title=payment_title,
            payment_description=payment_description,
        )
        self.assertEqual(payment.crypto, self.crypto)
        self.assertEqual(payment.fiat_amount, fait_amount)
        self.assertEqual(payment.fiat_currency, fiat_currency)
        self.assertEqual(payment.payment_title, payment_title)
        self.assertEqual(payment.payment_description, payment_description)
        self.assertEqual(payment.address, self.backend.generate_new_address(0))

    def test_new_address_generated_for_every_transaction(self):
        payment = create_new_payment(self.crypto, 10, "USD")
        payment_count = CryptoCurrencyPayment.objects.filter(crypto=self.crypto).count()
        self.assertEqual(
            payment.address, self.backend.generate_new_address(payment_count - 1)
        )
        payment_two = create_new_payment(self.crypto, 100, "EUR")
        payment_count = CryptoCurrencyPayment.objects.filter(crypto=self.crypto).count()
        self.assertEqual(
            payment_two.address, self.backend.generate_new_address(payment_count - 1)
        )
        payment_three = create_new_payment(self.crypto_two, 100, "EUR")
        payment_count = CryptoCurrencyPayment.objects.filter(
            crypto=self.crypto_two
        ).count()
        self.assertEqual(payment_count, 1)
        self.assertEqual(payment_three.address, self.backend.generate_new_address(0))

    def test_address_transaction_can_be_resued(self):
        initial_payment = create_new_payment(self.crypto, 10, "USD")
        initial_payment.status = CryptoCurrencyPayment.PAYMENT_PAID
        initial_payment.save()
        payment = create_new_payment(self.crypto, 10, "USD")
        payment_count = CryptoCurrencyPayment.objects.filter(crypto=self.crypto).count()
        self.assertEqual(
            payment.address, self.backend.generate_new_address(payment_count - 1)
        )
        payment.status = CryptoCurrencyPayment.PAYMENT_PAID
        payment.save()
        payment_two = create_new_payment(self.crypto, 100, "EUR", reuse_address=True)
        self.assertEqual(initial_payment.address, payment_two.address)

    def test_particular_address_index_used(self):
        payment = create_new_payment(self.crypto, 10, "USD", address_index=10)
        self.assertEqual(payment.address, self.backend.generate_new_address(10))

    def test_payment_created_with_generic_object(self):
        inv_obj = Invoice(title="Fake Invoice with payment")
        inv_obj.save()
        payment = create_new_payment(
            self.crypto_two, 122, "EUR", related_object=inv_obj
        )
        self.assertEqual(payment.content_object, inv_obj)
        self.assertEqual(payment, inv_obj.payments.all()[0])

    def test_payment_can_belongs_to_a_user(self):
        UserModel = get_user_model()
        user = UserModel.objects.create_user(username="Fake User")
        payment = create_new_payment(self.crypto_two, 122, "EUR", user=user)
        self.assertEqual(payment.user, user)
        self.assertEqual(payment, user.crypto_payments.all()[0])

    def test_create_payment_child(self):
        payment = create_new_payment(self.crypto, 10, "USD", address_index=6)
        child_payment = create_child_payment(payment, 5)
        self.assertEqual(child_payment.address, payment.address)
        self.assertEqual(child_payment.parent_payment, payment)
        self.assertEqual(payment.child_payment, child_payment)

    def test_child_payment_created_gets_generic_parent_object(self):
        inv_obj = Invoice(title="Fake Invoice with payment")
        inv_obj.save()
        payment = create_new_payment(
            self.crypto_two, 122, "EUR", related_object=inv_obj
        )
        child_payment = create_child_payment(payment, 5)
        self.assertEqual(child_payment.content_object, inv_obj)
        inv_pks = [inv.pk for inv in inv_obj.payments.all()]
        self.assertEqual(len(inv_pks), 2)
        self.assertIn(child_payment.pk, inv_pks)
        self.assertIn(payment.pk, inv_pks)

    def test_payment_paid_when_fiat_is_zero(self):
        payment = create_new_payment(self.crypto, 0, "USD")
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_PAID)

    def tearDown(self):
        pass
