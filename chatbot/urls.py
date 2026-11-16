# SPDX-FileCopyrightText: 2026 Pace Wisdom Solutions Pvt. Ltd.
# SPDX-License-Identifier: Apache-2.0

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet

router = DefaultRouter()
router.register(r"conversations", ConversationViewSet, basename="conversation")

urlpatterns = [
    path("", include(router.urls)),
]
