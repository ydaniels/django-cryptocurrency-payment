# -*- coding: utf-8 -*-
from uuid import uuid4

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from cryptocurrency_payment.app_settings import get_backend_config, get_backend_obj


def get_new_address(backend, index, address_type, derivation_path):
    backend.wallet.clean_derivation()
    backend.wallet.from_path("{}/{}".format(derivation_path, str(index)))
    return backend.wallet.dumps()['addresses'][address_type.lower()]

def create_child_payment(payment, fiat_amount):
    """
    Create a child payment from a particular payment. A child payment can be created for a particular underpaid amount
    :param payment: The parent payment
    :param amount: The new fiat_amount. fiat_currency is the same as parent fiat_currency
    :return: payment oj
    """
    child_payment = create_new_payment(
        payment.crypto,
        fiat_amount=fiat_amount,
        fiat_currency=payment.fiat_currency,
        payment_title=payment.payment_title,
        payment_description=payment.payment_description,
        related_object=payment.content_object,
        user=payment.user,
        parent_payment=payment,
    )
    payment.child_payment = child_payment
    payment.save()
    return child_payment


def create_new_payment(
    crypto,
    fiat_amount,
    fiat_currency,
    payment_title=None,
    payment_description=None,
    related_object=None,
    user=None,
    parent_payment=None,
    address_index=None,
    reuse_address=None,
):
    """
    Create a cryptocurrency payment by using this method instead of creating directly on through the main model
    It helps with generation of addresses and fait conversion. Call these method directly to create a payment
    :param crypto: The crypto in config this transaction belongs too
    :param fiat_amount: The fiat amount of this transaction
    :param fiat_currency: The fiat currency of this transaction
    :param payment_title: Title you want on the payment
    :param payment_description: Description of the payment
    :param related_object: A generic object of another model that can be linked to this payments payment can be accessed from the model with object.payments.
    :param user: User that owns the payment for non anonymous payment
    :param parent_payment: The parent payment for subpayment or underpaid payments
    :param address_index: Use a particular generated address index for address generation see merchant-wallet
    :return: payment obj
    """
    crypto_reuse_address = reuse_address or get_backend_config(
        crypto, key="REUSE_ADDRESS"
    )
    crypto_code = get_backend_config(crypto, key="CODE")
    backend_obj = get_backend_obj(crypto)

    crypto_amount = backend_obj.convert_from_fiat(fiat_amount, fiat_currency)
    address = None
    resuse_address = False
    related_object_id = None
    if related_object:
        related_object_id = related_object.pk
    if parent_payment:
        address = parent_payment.address
        resuse_address = True
    if not address and crypto_reuse_address is True:
        address = CryptoCurrencyPayment.get_crypto_reused_address(crypto)
        resuse_address = address is not None
    if not address:
        address_generated_count = (
            address_index or CryptoCurrencyPayment.get_address_used_count(crypto)
        )
        get_backend_config(crypto, key="CODE")
        ADDRESS_TYPE = get_backend_config(crypto, key="ADDRESS_TYPE")
        DEVRIVATION_PATH = get_backend_config(crypto, key="DERIVATION_PATH")
        address = get_new_address(backend=backend_obj, index=address_generated_count, address_type=ADDRESS_TYPE, derivation_path=DEVRIVATION_PATH)

    payment = CryptoCurrencyPayment(
        crypto=crypto,
        crypto_code=crypto_code,
        address=address,
        crypto_amount=crypto_amount,
        fiat_amount=fiat_amount,
        fiat_currency=fiat_currency,
        payment_title=payment_title,
        payment_description=payment_description,
        address_reused=resuse_address,
        user=user,
        object_id=related_object_id,
        content_object=related_object,
        parent_payment=parent_payment,
    )
    if fiat_amount == 0:
        payment.status = CryptoCurrencyPayment.PAYMENT_PAID
    payment.save()
    return payment


class CryptoCurrencyPayment(models.Model):
    """
    Cryptocurrencypayment model to handle all cryptocurrency transactions and transaction status
    underpaid balance payment are recorded as child payment with their parent linked
    """

    PAYMENT_PAID = "paid"
    PAYMENT_CANCELLED = "cancelled"
    PAYMENT_NEW = "new"
    PAYMENT_PROCESSING = "processing"

    TRANSACTION_STATUS = (
        (PAYMENT_NEW, "New"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_CANCELLED, "Cancelled"),
        (PAYMENT_PROCESSING, "Processing"),
    )
    id = models.UUIDField(
        default=uuid4, editable=False, primary_key=True, verbose_name="ID",
    )
    crypto = models.CharField(max_length=50)
    crypto_code = models.CharField(max_length=15, null=True)
    address = models.CharField(max_length=200)
    address_reused = models.BooleanField(default=False)
    tx_hash = models.CharField(max_length=150, null=True, help_text="Transaction ID")

    status = models.CharField(
        choices=TRANSACTION_STATUS, default=PAYMENT_NEW, max_length=50
    )

    crypto_amount = models.DecimalField(
        max_digits=17, decimal_places=12, help_text="Calculated crypto amount for fiat"
    )
    paid_crypto_amount = models.DecimalField(
        max_digits=17,
        decimal_places=12,
        help_text="Paid crypto amount",
        null=True,
        default=0,
    )
    fiat_amount = models.DecimalField(
        max_digits=9, decimal_places=2, help_text="Fiat amount"
    )
    fiat_currency = models.CharField(max_length=5, default="USD")
    payment_title = models.CharField(max_length=100, null=True)
    payment_description = models.CharField(max_length=250, null=True)
    user = models.ForeignKey(
        get_user_model(),
        null=True,
        on_delete=models.CASCADE,
        related_name="crypto_payments",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.CharField(null=True, max_length=100)
    content_object = GenericForeignKey("content_type", "object_id")
    parent_payment = models.OneToOneField(
        "self", null=True, on_delete=models.CASCADE, related_name="child"
    )
    child_payment = models.OneToOneField(
        "self", null=True, on_delete=models.SET_NULL, related_name="parent"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} {} {} {}".format(
            self.crypto_amount, self.address, self.fiat_amount, self.fiat_currency
        )

    @classmethod
    def get_crypto_reused_address(cls, crypto):
        """
        Get an address from old paid transaction when reusing address
        :param crypto: The crypto to get its address
        :return:
        """

        previous_payment = (
            cls.objects.filter(crypto=crypto, status=cls.PAYMENT_PAID)
            .order_by("updated_at")
            .first()
        )
        if previous_payment:
            address = previous_payment.address
            return address

    @classmethod
    def get_address_used_count(cls, crypto):
        """
        Get the total number of addresses generated for a particluar crypto currency
        :param crypto:
        :return:
        """
        return cls.objects.filter(crypto=crypto).count()

    @property
    def remaining_crypto_amount(self):
        if self.crypto_amount > self.paid_crypto_amount:
            return self.crypto_amount - self.paid_crypto_amount

    @property
    def is_under_paid(self):
        if self.paid_crypto_amount and self.remaining_crypto_amount:
            return True
        return False
