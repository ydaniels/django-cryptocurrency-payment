from django.db import models

# Put your test models here
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from cryptocurrency_payment.models import CryptoCurrencyPayment


class Invoice(models.Model):

    payments = GenericRelation(CryptoCurrencyPayment)
    title = models.CharField(max_length=50)
