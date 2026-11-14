# SPDX-FileCopyrightText: 2026 Pace Wisdom Solutions Pvt. Ltd.
# SPDX-License-Identifier: Apache-2.0

import time

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from accounts.views import _login_lockout_cache_keys
from organizations.models import Organization, OrganizationMember
from rbac.models import Role


PASSWORD = "valid-password-123"


@pytest.fixture
def login_user():
    user = User.objects.create_user(email="lockout@example.com", password=PASSWORD)
    organization = Organization.objects.create(name="Lockout Org", slug="lockout-org")
    role, _ = Role.objects.get_or_create(name="student")
    OrganizationMember.objects.create(
        organization=organization,
        user=user,
        role=role,
    )
    return user


@pytest.mark.django_db
def test_account_is_locked_in_cache_after_three_failed_logins(login_user, settings):
    settings.LOGIN_MAX_FAILED_ATTEMPTS = 3
    settings.LOGIN_LOCKOUT_MINUTES = 5
    client = APIClient()
    url = reverse("login")

    for _ in range(2):
        response = client.post(url, {"email": login_user.email, "password": "wrong"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.post(url, {"email": login_user.email, "password": "wrong"})
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert int(response["Retry-After"]) > 0

    _, lock_key = _login_lockout_cache_keys(login_user)
    assert cache.get(lock_key) is not None

    # A correct password cannot bypass an active lock.
    response = client.post(url, {"email": login_user.email, "password": PASSWORD})
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_successful_login_resets_cached_failed_attempts(login_user):
    client = APIClient()
    url = reverse("login")

    response = client.post(url, {"email": login_user.email, "password": "wrong"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.post(url, {"email": login_user.email, "password": PASSWORD})
    assert response.status_code == status.HTTP_200_OK

    attempts_key, lock_key = _login_lockout_cache_keys(login_user)
    assert cache.get(attempts_key) is None
    assert cache.get(lock_key) is None


@pytest.mark.django_db
def test_login_is_allowed_after_cached_lock_expires(login_user):
    _, lock_key = _login_lockout_cache_keys(login_user)
    cache.set(lock_key, time.time() - 1, timeout=60)

    response = APIClient().post(
        reverse("login"),
        {"email": login_user.email, "password": PASSWORD},
    )
    assert response.status_code == status.HTTP_200_OK
    assert cache.get(lock_key) is None
