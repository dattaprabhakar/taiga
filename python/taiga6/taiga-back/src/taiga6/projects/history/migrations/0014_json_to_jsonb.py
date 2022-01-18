# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos Ventures SL

# Generated by Django 1.10.2 on 2016-10-26 11:34
from __future__ import unicode_literals

from django.db import migrations
from django.db.models import JSONField


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0013_historyentry_values_diff_cache'),
    ]

    operations = [
        migrations.RunSQL(
            """
                ALTER TABLE "history_historyentry"
                   ALTER COLUMN "delete_comment_user"
                           TYPE jsonb
                          USING regexp_replace("delete_comment_user"::text, '[\\\\]+u0000', '\\\\\\\\u0000', 'g')::jsonb,

                   ALTER COLUMN "comment_versions"
                           TYPE jsonb
                          USING regexp_replace("comment_versions"::text, '[\\\\]+u0000', '\\\\\\\\u0000', 'g')::jsonb,

                   ALTER COLUMN "values_diff_cache"
                           TYPE jsonb
                          USING regexp_replace("values_diff_cache"::text, '[\\\\]+u0000', '\\\\\\\\u0000', 'g')::jsonb,

                   ALTER COLUMN "user"
                           TYPE jsonb
                          USING regexp_replace("user"::text, '[\\\\]+u0000', '\\\\\\\\u0000', 'g')::jsonb,

                   ALTER COLUMN "diff"
                           TYPE jsonb
                          USING regexp_replace("diff"::text, '[\\\\]+u0000', '\\\\\\\\u0000', 'g')::jsonb,

                   ALTER COLUMN "snapshot"
                           TYPE jsonb
                          USING regexp_replace("snapshot"::text, '[\\\\]+u0000', '\\\\\\\\u0000', 'g')::jsonb,

                   ALTER COLUMN "values"
                           TYPE jsonb
                          USING regexp_replace("values"::text, '[\\\\]+u0000', '\\\\\\\\u0000', 'g')::jsonb;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
    ]
