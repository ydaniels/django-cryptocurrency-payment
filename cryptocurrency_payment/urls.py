# -*- coding: utf-8 -*-
from django.urls import path

from cryptocurrency_payment import views

app_name = 'cryptocurrency_payment'
urlpatterns = [

    path(
        "payment/<uuid:pk>/",
        view=views.CryptoPaymentDetailView.as_view(),
        name='crypto_payment_detail',
    ),

]
