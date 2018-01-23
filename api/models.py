from __future__ import unicode_literals

from django.db import models


class TokenDatabase(models.Model):
    uuid = models.CharField('uuid', max_length=200, primary_key=True)
    code = models.CharField('code', max_length=200)
    username = models.CharField('username', max_length=200)
    password = models.CharField('password', max_length=200)
    url = models.URLField('url')
