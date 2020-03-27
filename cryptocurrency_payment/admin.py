# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import (
   CryptoCurrencyPayment
)


@admin.register(CryptoCurrencyPayment)
class CrptoCurrancyPaymentAdmin(admin.ModelAdmin):
    pass



