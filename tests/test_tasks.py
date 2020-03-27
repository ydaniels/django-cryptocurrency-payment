from datetime import timedelta
import sys

if sys.version_info >= (3, 3):

    from unittest import mock
else:
    import mock

from django.test import TestCase
from django.utils import timezone
from cryptocurrency_payment.models import create_new_payment, CryptoCurrencyPayment
from cryptocurrency_payment.tasks import (
    cancel_unpaid_payment,
    refresh_payment_prices,
    update_payment_status,
    CryptoCurrencyPaymentTask,
)

from merchant_wallet.backends.btc import BitcoinBackend


fake_payment_paid_status = [
    (BitcoinBackend.UNCONFIRMED_ADDRESS_BALANCE, "hash"),
    (BitcoinBackend.CONFIRMED_ADDRESS_BALANCE, 123),
]
underpaid_payment_status = [
    (BitcoinBackend.UNDERPAID_ADDRESS_BALANCE, 1),
    (BitcoinBackend.UNDERPAID_ADDRESS_BALANCE, 3),
]
no_payment_status = [(BitcoinBackend.NO_HASH_ADDRESS_BALANCE, None)]


class TestCryptocurrencyTask(TestCase):
    def setUp(self):
        self.crypto = "BITCOIN"

    def test_cancel_old_payment(self):
        payment = create_new_payment(self.crypto, 10, "USD")
        payment_two = create_new_payment(self.crypto, 10, "USD")
        created_at = timezone.now() - timedelta(hours=48)
        CryptoCurrencyPayment.objects.filter(pk=payment_two.pk).update(
            created_at=created_at
        )
        payment_task = CryptoCurrencyPaymentTask(self.crypto)
        payment_task.cancel_unpaid_payment()
        payment_two.refresh_from_db()
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_NEW)
        self.assertEqual(payment_two.status, CryptoCurrencyPayment.PAYMENT_CANCELLED)

    def test_cancel_old_payment_task(self):
        payment = create_new_payment(self.crypto, 10, "USD")
        payment_two = create_new_payment(self.crypto, 10, "USD")
        created_at = timezone.now() - timedelta(hours=48)
        CryptoCurrencyPayment.objects.filter(pk=payment_two.pk).update(
            created_at=created_at
        )
        cancel_unpaid_payment()
        payment_two.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_NEW)
        self.assertEqual(payment_two.status, CryptoCurrencyPayment.PAYMENT_CANCELLED)

    @mock.patch(
        "merchant_wallet.backends.btc.BitcoinBackend.convert_from_fiat",
        side_effect=[20, 50],
    )
    def test_prices_get_refreshed(self, convert_fiat_side):
        payment = create_new_payment(self.crypto, 10, "USD")
        self.assertEqual(payment.crypto_amount, 20)
        payment_task = CryptoCurrencyPaymentTask(self.crypto)
        payment_task.refresh_new_crypto_payment_amount()
        payment.refresh_from_db()
        self.assertEqual(payment.crypto_amount, 20)
        updated_at = timezone.now() - timedelta(minutes=1000)
        CryptoCurrencyPayment.objects.filter(pk=payment.pk).update(
            updated_at=updated_at
        )
        payment_task.refresh_new_crypto_payment_amount()
        payment.refresh_from_db()
        self.assertEqual(payment.crypto_amount, 50)

    @mock.patch(
        "merchant_wallet.backends.btc.BitcoinBackend.convert_from_fiat",
        side_effect=[20, 50],
    )
    def test_refresh_prices_task(self, convert_fiat_side):
        payment = create_new_payment(self.crypto, 10, "USD")
        self.assertEqual(payment.crypto_amount, 20)
        refresh_payment_prices()
        payment.refresh_from_db()
        self.assertEqual(payment.crypto_amount, 20)
        updated_at = timezone.now() - timedelta(minutes=1000)
        CryptoCurrencyPayment.objects.filter(pk=payment.pk).update(
            updated_at=updated_at
        )
        refresh_payment_prices()
        payment.refresh_from_db()
        self.assertEqual(payment.crypto_amount, 50)

    @mock.patch(
        "merchant_wallet.backends.btc.BitcoinBackend.confirm_address_payment",
        side_effect=fake_payment_paid_status,
    )
    def test_payment_status_processing_update(self, fake_payment_paid):
        payment = create_new_payment(self.crypto, 10, "USD")
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_NEW)
        payment_task = CryptoCurrencyPaymentTask(self.crypto)
        payment_task.update_crypto_currency_payment_status()
        payment.refresh_from_db()
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_PROCESSING)
        self.assertEqual(payment.tx_hash, "hash")
        payment_task.update_crypto_currency_payment_status()
        payment.refresh_from_db()
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_PAID)
        self.assertEqual(payment.paid_crypto_amount, 123)

    @mock.patch(
        "merchant_wallet.backends.btc.BitcoinBackend.confirm_address_payment",
        side_effect=fake_payment_paid_status,
    )
    def test_payment_status_paid_task_update(self, fake_payment_paid):
        payment = create_new_payment(self.crypto, 10, "USD")
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_NEW)
        update_payment_status()
        payment.refresh_from_db()
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_PROCESSING)
        self.assertEqual(payment.tx_hash, "hash")
        update_payment_status()
        payment.refresh_from_db()
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_PAID)
        self.assertEqual(payment.paid_crypto_amount, 123)

    @mock.patch(
        "merchant_wallet.backends.btc.BitcoinBackend.convert_to_fiat",
        side_effect=[2, 150],
    )
    @mock.patch(
        "merchant_wallet.backends.btc.BitcoinBackend.confirm_address_payment",
        side_effect=underpaid_payment_status,
    )
    def test_payment_status_no_underpaid_payment(
        self, fake_payment_paid, convert_to_fiat
    ):
        payment = create_new_payment(self.crypto, 10, "USD")
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_NEW)
        payment_task = CryptoCurrencyPaymentTask(self.crypto)
        payment_task.update_crypto_currency_payment_status()
        payment.refresh_from_db()
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_PAID)
        self.assertEqual(payment.paid_crypto_amount, 1)
        self.assertIsNone(payment.child_payment)

    @mock.patch(
        "merchant_wallet.backends.btc.BitcoinBackend.convert_to_fiat",
        side_effect=[150, 1],
    )
    @mock.patch(
        "merchant_wallet.backends.btc.BitcoinBackend.confirm_address_payment",
        side_effect=underpaid_payment_status,
    )
    def test_payment_status_created_underpaid_payment(
        self, fake_payment_paid, convert_to_fiat
    ):
        payment = create_new_payment(self.crypto, 10, "USD")
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_NEW)
        payment_task = CryptoCurrencyPaymentTask(self.crypto)
        payment_task.update_crypto_currency_payment_status()
        payment.refresh_from_db()
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_PAID)
        self.assertEqual(payment.paid_crypto_amount, 1)
        self.assertIsNotNone(payment.child_payment)
        self.assertEqual(payment.child_payment.parent_payment, payment)

    @mock.patch(
        "merchant_wallet.backends.btc.BitcoinBackend.confirm_address_payment",
        side_effect=no_payment_status,
    )
    def test_payment_cancelled_when_no_hash(self, fake_payment_paid):
        payment = create_new_payment(self.crypto, 10, "USD")
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_NEW)
        payment_task = CryptoCurrencyPaymentTask(self.crypto)
        payment_task.update_crypto_currency_payment_status()
        payment.refresh_from_db()
        self.assertEqual(payment.status, CryptoCurrencyPayment.PAYMENT_CANCELLED)
