# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos Ventures SL

from fastapi import UploadFile
from pydantic import validator
from taiga.base.serializer import BaseModel
from taiga.base.utils.images import valid_content_type, valid_image_format
from taiga.base.validator import as_form


@as_form
class ProjectValidator(BaseModel):
    name: str
    workspace_slug: str
    description: str | None = None
    color: int | None = None
    logo: UploadFile | None = None

    @validator("name")
    def check_name_not_empty(cls, v: str) -> str:
        assert v != "", "Empty name is not allowed"
        return v

    @validator("name")
    def check_name_length(cls, v: str) -> str:
        assert len(v) <= 80, "Name too long"
        return v

    @validator("description")
    def check_description_length(cls, v: str | None) -> str | None:
        if v:
            assert len(v) <= 200, "Description too long"
        return v

    @validator("color")
    def check_allowed_color(cls, v: int | None) -> int | None:
        if v:
            assert v >= 1 and v <= 8, "Color not allowed"
        return v

    @validator("logo")
    def check_content_type(cls, v: UploadFile | None) -> UploadFile | None:
        if v:
            assert valid_content_type(v), "Invalid image format"
        return v

    @validator("logo")
    def check_image_format(cls, v: UploadFile | None) -> UploadFile | None:
        if v:
            assert valid_image_format(v), "Invalid image content"
        return v

    # Sanitizers

    @validator("name")
    def strip_name(cls, v: str) -> str:
        return v.strip()


class PermissionsValidator(BaseModel):
    permissions: list[str]
