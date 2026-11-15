# SPDX-FileCopyrightText: 2026 Pace Wisdom Solutions Pvt. Ltd.
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.views import AcceptInviteView, ForgotPasswordView, LoginView, ResetPasswordView


def _limit(scope):
    return int(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][scope].split("/")[0])


@pytest.mark.parametrize(
    "view, scope",
    [
        (ForgotPasswordView, "auth_password_reset_email"),
        (ResetPasswordView, "auth_token"),
        (AcceptInviteView, "auth_token"),
    ],
)
def test_auth_views_are_throttled(view, scope):
    assert view.throttle_scope == scope
    assert scope in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]


def test_login_has_no_per_ip_rate_limit(settings):
    assert LoginView.throttle_classes == []
    assert "auth_login" not in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]


@pytest.mark.django_db
@patch("accounts.views._send_password_reset_link")
def test_forgot_password_is_rate_limited(mock_send):
    client = APIClient()
    url = reverse("forgot_password")

    for _ in range(_limit("auth_password_reset_email")):
        response = client.post(url, {"email": "someone@example.com"}, format="json")
        assert response.status_code == status.HTTP_200_OK

    response = client.post(url, {"email": "someone@example.com"}, format="json")
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_reset_password_is_rate_limited():
    client = APIClient()
    url = reverse("reset_password")
    payload = {"token": "invalid-token", "password": "NewPassw0rd!x", "confirm_password": "NewPassw0rd!x"}

    for _ in range(_limit("auth_token")):
        response = client.post(url, payload, format="json")
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    response = client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
