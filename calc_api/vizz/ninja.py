import logging
from typing import List

from django.middleware import csrf

from ninja import NinjaAPI, Router, Schema

from calc_api.config import ClimadaCalcApiConfig
from calc_api.vizz import schemas, schemas_widgets, schemas_geocoding
from calc_api.vizz.util import get_options
from calc_api.vizz.models import JobLog
from calc_api.calc_methods import geocode, widget_costbenefit
from calc_api.job_management.standardise_schema import standardise_schema

conf = ClimadaCalcApiConfig()

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(getattr(logging, conf.LOG_LEVEL))


description = f"""
<table>
  <tr>
    <td>
      GitLab:
      <a target=_blank href={conf.REPOSITORY_URL}>
        climada-data-api
      </a>
    </td>
    <td>
      <a target=_blank href={conf.LOGO_LINK}>
        <img src={conf.LOGO_SRC} height=100>
      </a>
    </td>
  </tr>
</table>
"""


_default = NinjaAPI(
    title='CLIMADA Calc API',
    urls_namespace='vizz',
    description=description,
    #renderer=renderers.SchemaJSONRenderer()
)


_api = Router()


@_api.get(
    "/options",
    tags=["options"],
    summary="Options in the RECA web tool"
)
def _api_get_options(request=None):
    return get_options()


@_api.get("/geocode/autocomplete",
          tags=["geocode"],
          response=schemas_geocoding.GeocodePlaceList,
          summary="Get suggested locations from a string")
def _api_geocode_autocomplete(request, query):
    return geocode.geocode_autocomplete(query)


@_api.get("/geocode/reca_locations",
          tags=["geocode"],
          response=schemas_geocoding.GeocodePlaceList,
          summary="Get list of locations that have precalculated data")
def _api_geocode_precalculated_locations(request):
    return geocode.geocode_precalculated_locations()


#######################################
#
#   WIDGETS
#
#######################################


@_api.get(
    "/widgets/default-measures",
    tags=["widget"],
    response=List[schemas.MeasureSchema],
    summary="Get predefined adaptation measures"
)
def _api_default_measures(request, measure_id: int = None, slug: str = None, hazard_type: str = None, exposure_type: str = None):
    return widget_costbenefit.get_default_measures(measure_id, slug, hazard_type, exposure_type)


# ----- COST-BENEFIT ------

@_api.post(
    "/widgets/cost-benefit",
    tags=["widget"],
    response=schemas_widgets.CostBenefitWidgetJobSchema,
    summary="Create data for the cost-benefit section of the RECA site"
)
@standardise_schema
def _api_widget_costbenefit_submit(request, data: schemas_widgets.CostBenefitWidgetRequest):
    result = JobLog.objects.get(job_hash=str(data.get_id()))
    return schemas_widgets.CostBenefitWidgetJobSchema.from_joblog(result, 'rest/vizz/widgets/cost-benefit')


@_api.get(
    "/widgets/cost-benefit/{uuid:job_id}",
    tags=["widget"],
    response=schemas_widgets.CostBenefitWidgetJobSchema,
    summary="Get precalculated data for the cost-benefit section of the RECA site"
)
def _api_widget_costbenefit_poll(request, job_id):
    result = JobLog.objects.get(job_hash=str(job_id))
    return schemas_widgets.CostBenefitWidgetJobSchema.from_joblog(result, 'rest/vizz/widgets/cost-benefit')


# ----- RISK TIMELINE ------

@_api.post(
    "/widgets/risk-timeline",
    tags=["widget"],
    response=schemas_widgets.TimelineWidgetJobSchema,
    summary="Create data for the risk over time section of the RECA site"
)
@standardise_schema
def _api_widget_risk_timeline_submit(request, data: schemas_widgets.TimelineWidgetRequest):
    result = JobLog.objects.get(job_hash=str(data.get_id()))
    return schemas_widgets.TimelineWidgetJobSchema.from_joblog(result, 'rest/vizz/widgets/risk-timeline')


@_api.get(
    "/widgets/risk-timeline/{uuid:job_id}",
    tags=["widget"],
    response=schemas_widgets.TimelineWidgetJobSchema,
    summary="Get precalculated risk over time data for the RECA site"
)
def _api_widget_risk_timeline_poll(request, job_id):
    result = JobLog.objects.get(job_hash=str(job_id))
    return schemas_widgets.TimelineWidgetJobSchema.from_joblog(result, 'rest/vizz/widgets/risk-timeline')


# ----- BIODIVERSITY ------

@_api.post(
    "/widgets/biodiversity",
    tags=["widget"],
    response=schemas_widgets.BiodiversityWidgetJobSchema,
    summary="Create data for the biodiversity section of the RECA site"
)
@standardise_schema
def _api_widget_biodiversity_submit(request, data: schemas_widgets.BiodiversityWidgetRequest):
    result = JobLog.objects.get(job_hash=str(data.get_id()))
    return schemas_widgets.BiodiversityWidgetJobSchema.from_joblog(result, 'rest/vizz/widgets/biodiversity')


@_api.get(
    "/widgets/biodiversity/{uuid:job_id}",
    tags=["widget"],
    response=schemas_widgets.BiodiversityWidgetJobSchema,
    summary="Get precalculated data for the biodiversity section of the RECA site"
)
def _api_widget_biodiversity_poll(request, job_id):
    result = JobLog.objects.get(job_hash=str(job_id))
    return schemas_widgets.BiodiversityWidgetJobSchema.from_joblog(result, 'rest/vizz/widgets/biodiversity')


# ----- SOCIAL VULNERABILITY ------

@_api.post(
    "/widgets/social-vulnerability",
    tags=["widget"],
    response=schemas_widgets.SocialVulnerabilityWidgetJobSchema,
    summary="Create data for the social vulnerability section of the RECA site"
)
@standardise_schema
def _api_widget_social_vulnerability_submit(request, data: schemas_widgets.SocialVulnerabilityWidgetRequest):
    result = JobLog.objects.get(job_hash=str(data.get_id()))
    return schemas_widgets.SocialVulnerabilityWidgetJobSchema.from_joblog(result, 'rest/vizz/widgets/social-vulnerability')


@_api.get(
    "/widgets/social-vulnerability/{uuid:job_id}",
    tags=["widget"],
    response=schemas_widgets.SocialVulnerabilityWidgetJobSchema,
    summary="Get precalculated data for the social vulnerability section of the RECA site"
)
def _api_widget_social_vulnerability_poll(request, job_id):
    result = JobLog.objects.get(job_hash=str(job_id))
    return schemas_widgets.SocialVulnerabilityWidgetJobSchema.from_joblog(result, 'rest/vizz/widgets/social-vulnerability')


_default.add_router("/", _api)
resturls = _default.urls
