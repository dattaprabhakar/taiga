# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos Ventures SL


import pytest
from fastapi import status
from taiga.auth.tokens import RefreshToken
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


async def test_login_successfuly(client):
    password = "test_password"
    user = await f.create_user(password=password)

    data = {
        "username": user.username,
        "password": password,
    }

    response = client.post("/auth/token", json=data)
    assert response.status_code == 200, response.text
    assert response.json().keys() == {"token", "refresh"}


def test_login_error_invalid_credentials(client):
    data = {
        "username": "test_non_existing_user",
        "password": "test_password",
    }

    response = client.post("/auth/token", json=data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.headers["www-authenticate"] == 'Bearer realm="api"'


async def test_refresh_successfuly(client):
    user = await f.create_user(is_active=True)
    token = await RefreshToken.create_for_user(user)
    data = {
        "refresh": str(token),
    }

    response = client.post("/auth/token/refresh", json=data)
    assert response.status_code == 200, response.text
    assert response.json().keys() == {"token", "refresh"}


def test_refresh_error_invalid_token(client):
    data = {"refresh": "invalid_token"}

    response = client.post("/auth/token/refresh", json=data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
