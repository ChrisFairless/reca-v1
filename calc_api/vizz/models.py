import datetime as dt
import uuid
import datetime

from django.db import models
from calc_api.config import ClimadaCalcApiConfig

conf = ClimadaCalcApiConfig()


class JobLog(models.Model):
    job_hash = models.CharField(max_length=36, primary_key=True, db_index=True)
    func = models.CharField(max_length=50)
    args = models.TextField()
    kwargs = models.TextField()
    result = models.JSONField(null=True)


class Cobenefit(models.Model):
    value = models.TextField(primary_key=True)
    name = models.TextField()
    description = models.TextField(null=True)


class Measure(models.Model):
    name = models.TextField()
    slug = models.TextField(null=True)
    description = models.TextField(null=True)
    hazard_type = models.TextField()
    exposure_type = models.TextField(null=True)
    cost_type = models.TextField(default="whole_project")
    cost = models.FloatField()
    annual_upkeep = models.FloatField(default=0)
    priority = models.TextField(default="even_coverage")
    percentage_coverage = models.FloatField(default=100)
    percentage_effectiveness = models.FloatField(default=100)
    is_coastal = models.BooleanField(default=False)
    max_distance_from_coast = models.FloatField(null=True)
    hazard_cutoff = models.FloatField(null=True)
    return_period_cutoff = models.FloatField(null=True)
    hazard_change_multiplier = models.FloatField(null=True)
    hazard_change_constant = models.FloatField(null=True)
    cobenefits = models.ManyToManyField(Cobenefit, null=True)
    units_currency = models.TextField()
    units_hazard = models.TextField()
    units_distance = models.TextField()
    user_generated = models.BooleanField()


class Location(models.Model):
    name = models.TextField(primary_key=True)
    # TODO decide what the ID is for and use it consistently
    id = models.TextField()
    scale = models.CharField(max_length=15, null=True)
    country = models.CharField(max_length=60, null=True)
    country_id = models.CharField(max_length=3, null=True)
    admin1 = models.CharField(max_length=60, null=True)
    admin1_id = models.CharField(max_length=15, null=True)
    admin2 = models.CharField(max_length=60, null=True)
    admin2_id = models.CharField(max_length=15, null=True)
    bbox = models.TextField(null=True)
    poly = models.TextField(null=True)


class SSP_GDP(models.Model):
    scenario = models.CharField(max_length=4)
    region = models.CharField(max_length=3)
    year = models.IntegerField()
    growth = models.FloatField()
