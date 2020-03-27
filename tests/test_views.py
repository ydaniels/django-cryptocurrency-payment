from django.test import TestCase
from django.shortcuts import reverse
from django.contrib.auth import get_user_model
from cryptocurrency_payment.models import create_new_payment, create_child_payment


class TestCryptocurrencyView(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user_obj = User.objects.create_user(username="Fake_user")
        self.user_two_obj = User.objects.create_user(username="Fake_user_2")
        self.user_payment = create_new_payment("BITCOIN", 10, "USD", user=self.user_obj)
        self.anon_payment = create_new_payment("BITCOIN", 10, "USD")
        self.no_anon_payment = create_new_payment("BITCOINTEST", 10, "USD")

    def test_anon_can_see_payment_allowed(self):

        url = reverse(
            "cryptocurrency_payment:crypto_payment_detail", args=(self.anon_payment.pk,)
        )
        create_child_payment(self.anon_payment, 50)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_anon_cannot_see_payment_not_allowed(self):
        url = reverse(
            "cryptocurrency_payment:crypto_payment_detail",
            args=(self.no_anon_payment.pk,),
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_anon_cannot_see_user_payment(self):
        url = reverse(
            "cryptocurrency_payment:crypto_payment_detail", args=(self.user_payment.pk,)
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_see_other_user_payment(self):
        url = reverse(
            "cryptocurrency_payment:crypto_payment_detail", args=(self.user_payment.pk,)
        )
        self.client.force_login(self.user_two_obj)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_user_can_see_own_payment(self):
        url = reverse(
            "cryptocurrency_payment:crypto_payment_detail", args=(self.user_payment.pk,)
        )
        self.client.force_login(self.user_obj)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
