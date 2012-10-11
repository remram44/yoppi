from django.db import models


class IndexerParameter(models.Model):
    name = models.CharField(
            "parameter name",
            primary_key=True, max_length=20,
            blank=False)
    value = models.CharField(
            "parameter value",
            max_length=100,
            blank=True)
