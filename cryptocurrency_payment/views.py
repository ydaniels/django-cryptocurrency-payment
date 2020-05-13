# -*- coding: utf-8 -*-
from django.views.generic import DetailView
from django.http import Http404
from cryptocurrency_payment.models import CryptoCurrencyPayment
from cryptocurrency_payment.app_settings import get_backend_config


class CryptoPaymentDetailView(DetailView):
    queryset = CryptoCurrencyPayment.objects.all()
    context_object_name = 'payment'
    template_name = 'cryptocurrency_payment/payment_detail.html'

    def get_object(self, *args ):

        obj = super(CryptoPaymentDetailView, self).get_object( *args )
        allow_anon_payment = get_backend_config(obj.crypto, key='ALLOW_ANONYMOUS_PAYMENT')
        if  allow_anon_payment is not True and   self.request.user.is_authenticated is not True:
            raise Http404
        elif   obj.user and self.request.user != obj.user:
            raise Http404
        return obj
