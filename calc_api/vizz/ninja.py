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
from calc_api.job_management.wrangle_units import wrangle_endpoint_units

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


@_api.get("/geocode/id/{str:id}",
          tags=["geocode"],
          response=schemas_geocoding.GeocodePlace,
          summary="Convert place name or ID into geocoded object")
def _api_geocode_place(request, id):
    return geocode.location_from_code(location_code=id)


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


# TODO convert measures units nicely
@_api.get(
    "/widgets/default-measures",
    tags=["widget"],
    response=List[schemas.MeasureSchema],
    summary="Get predefined adaptation measures"
)
def _api_default_measures(
        request,
        measure_id: int = None,
        slug: str = None,
        hazard_type: str = None,
        exposure_type: str = None,
        units_hazard: str = None,
        units_currency: str = None,
        units_distance: str = None
):
    return widget_costbenefit.get_default_measures(
        measure_id,
        slug,
        hazard_type,
        exposure_type,
        units_hazard,
        units_currency,
        units_distance
    )


# ----- COST-BENEFIT ------

@_api.post(
    "/widgets/cost-benefit",
    tags=["widget"],
    response=schemas_widgets.CostBenefitWidgetJobSchema,
    summary="Create data for the cost-benefit section of the RECA site"
)
@standardise_schema
@wrangle_endpoint_units
def _api_widget_costbenefit_submit(request, data: schemas_widgets.CostBenefitWidgetRequest):
    if data.hazard_type == "tropical_cyclone":
        result = JobLog.objects.get(job_hash=str(data.get_id()))
        return schemas_widgets.CostBenefitWidgetJobSchema.from_joblog(result, 'rest/vizz/widgets/cost-benefit')
    else:
        import json
        location_root = 'rest/vizz/widgets/cost-benefit'
        result_json = '''
        {
            "job_id": "d5fa024e-3c81-9aa6-53c0-0a958b513b4f",
            "location": "rest/vizz/widgets/cost-benefit/d5fa024e-3c81-9aa6-53c0-0a958b513b4f",
            "status": "SUCCESS",
            "request": {},
            "submitted_at": null,
            "completed_at": null,
            "expires_at": null,
            "response": {
                "data": {
                    "text": [
                        {
                            "template": "Climate adaptation measures can either reduce the intensity of hazards or the impacts that hazards have. While it's hard to model the adaptation measures at single locations without dedicated feasibility studies, we can give first-guess, indicative numbers for the effectiveness of urban greening.    ",
                            "values": []
                        },
                        {
                            "template": "Increasing green cover in a city creates shade to keep people of of direct sun while in the street, and evapotranspirative cooling from the leaves which reduces the temperatures locally. Urban greening is a biodiverse solution which can also reduce flooding risk and improve neighborhood values and wellbeing. The benefits of tree cover are very dependent on the trees planted and local climate.",
                            "values": []
                        },
                        {
                            "template": "By adapting with urban greening there is an average estimated decrease of {{measure_benefit}} affected by the impacts of extreme heat each year, using a 2020 baseline.",
                            "values": [
                                {
                                    "key": "measure_benefit",
                                    "value": 224558.79562570148,
                                    "units": "person-days"
                                }
                            ]
                        },
                        {
                            "template": "Projecting forward with climate change and growth, the effect increases by {{future_measure_percentage_change}}: in 2080 the measure gives a decrease of {{measure_future_benefit}} affected in an average year under the SSP2 4.5 (middle of the road) scenario.",
                            "values": [
                                {
                                    "key": "future_measure_percentage_change",
                                    "value": 127.99360097648717,
                                    "units": "%"
                                },
                                {
                                    "key": "measure_future_benefit",
                                    "value": 509746.905335617197,
                                    "units": "person-days"
                                }
                            ]
                        },
                        {
                            "template": "This means that, over {{n_years_of_analysis}} until 2080, and at a cost of {{measure_cost}}, implementing urban greening saves (very roughly) {{saved_per_unit_currency}} affected for each USD spent.",
                            "values": [
                                {
                                    "key": "n_years_of_analysis",
                                    "value": 60.0,
                                    "units": "years"
                                },
                                {
                                    "key": "measure_cost",
                                    "value": 50000000.0,
                                    "units": "USD"
                                },
                                {
                                    "key": "saved_per_unit_currency",
                                    "value": 724430.820576791204,
                                    "units": "person-days"
                                }
                            ]
                        },
                        {
                            "template": "Remember: these numbers are intended as guidance only - they are based on global climate models and global impact models. Inevitably the situations in individual places will be different from the global assumptions that go into these models. They're not a substitute for local feasibility studies, which should be the next step.",
                            "values": []
                        }
                    ],
                    "chart": {
                        "items": [
                            {
                                "year_label": "2080",
                                "year_value": 2080.0,
                                "temperature": -1798.1999999999998,
                                "current_climate": 3374342.477,
                                "growth_change": 1031533.1208764231,
                                "climate_change": 2106372.66751636,
                                "future_climate": 6512247.06189412,
                                "measure_names": [
                                    "Urban greening"
                                ],
                                "measure_change": [
                                    -509746.28205679265
                                ],
                                "measure_climate": [
                                    6002501.905335617197
                                ],
                                "combined_measure_change": null,
                                "combined_measure_climate": null
                            }
                        ],
                        "legend": {
                            "title": "Components of extreme_heat climate risk with measures Urban greening: annual average impact",
                            "units": "people",
                            "items": [
                                {
                                    "label": "Risk today",
                                    "slug": "current_climate",
                                    "value": 3374342.392344977594
                                },
                                {
                                    "label": "change from growth",
                                    "slug": "growth_change",
                                    "value": 1031533.489324543902
                                },
                                {
                                    "label": "change from climate change",
                                    "slug": "climate_change",
                                    "value": 2106372.305722888352
                                },
                                {
                                    "label": "change from adaptation measure: Urban greening",
                                    "slug": "adaptation_0",
                                    "value": -509746.28205679265
                                }
                            ]
                        },
                        "measure": [
                            {
                                "id": 34,
                                "name": "Urban greening",
                                "slug": "urban_greening_eh_people",
                                "description": "Increasing green cover in a city creates shade to keep people of of direct sun while in the street, and evapotranspirative cooling from the leaves which reduces the temperatures locally. Urban greening is a biodiverse solution which can also reduce flooding risk and improve neighborhood values and wellbeing. The benefits of tree cover are very dependent on the trees planted and local climate.",
                                "hazard_type": "extreme_heat",
                                "exposure_type": "people",
                                "cost_type": "whole_project",
                                "cost": 50000000.0,
                                "annual_upkeep": 0.0,
                                "priority": "even_coverage",
                                "percentage_coverage": 100.0,
                                "percentage_effectiveness": 100.0,
                                "is_coastal": false,
                                "max_distance_from_coast": 0.0,
                                "hazard_cutoff": 31.999999999999936,
                                "return_period_cutoff": null,
                                "hazard_change_multiplier": 1,
                                "hazard_change_constant": -0.8,
                                "cobenefits": null,
                                "units_currency": "USD",
                                "units_hazard": "degF",
                                "units_distance": "km",
                                "user_generated": false
                            }
                        ],
                        "cost": [
                            50000000.0                        ],
                        "costbenefit": [
                            724430.820576791204
                        ],
                        "combined_cost": null,
                        "combined_costbenefit": null,
                        "units_currency": "USD",
                        "units_warming": "degC",
                        "units_response": "people"
                    }
                },
                "metadata": {
                    "description": ""
                }
            },
            "response_uri": null,
            "code": null,
            "message": null
        }
        '''
        result = json.loads(result_json)
        output = schemas_widgets.CostBenefitWidgetJobSchema(
            job_id=result['job_id'],
            location=location_root + '/' + result['job_id'],
            status="SUCCESS",
            request={},  # TODO work out where to get this from
            completed_at=None,
            expires_at=None,
            response=result['response'],
            response_uri=None,
            code=None,
            message=None
        )
        return output

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
@wrangle_endpoint_units
def _api_widget_risk_timeline_submit(request, data: schemas_widgets.TimelineWidgetRequest):
    if data.hazard_type == "tropical_cyclone":
        result = JobLog.objects.get(job_hash=str(data.get_id()))
        return schemas_widgets.TimelineWidgetJobSchema.from_joblog(result, 'rest/vizz/widgets/risk-timeline')
    else:
        location_root = 'rest/vizz/widgets/risk-timeline'
        result_json = '''
            {
        "job_id": "d37dc547-d180-6d4a-9401-78775b1951b6",
        "location": "rest/vizz/widgets/risk-timeline/d37dc547-d180-6d4a-9401-78775b1951b6",
        "status": "SUCCESS",
        "request": {},
        "submitted_at": null,
        "completed_at": null,
        "expires_at": null,
        "response": {
            "data": {
                "text": [
                    {
                        "template": "Heatwaves are one of the deadliest natural disasters globally. Heat stress causes illness and death and slows economic activity.",
                        "values": []
                    },
                    {
                        "template": "In this analysis, we define a heatwave as a temperature which is above the 99th percentile of the recent historical temperature record. That means that in the 20th century people would experience about three days of heatwaves in a year. We measure the impacts of heatwaves in 'person-days'. This is the number of days of extreme heat experienced by all people in the population we're looking at. So one person would historically expect three person-days of heatwaves in a year. And a thousand people would experience 3,000 person-days of heat. But if the climate warms and there are eight heatwave days in a future year, then the population of a thousand would experience 8,000 person-days of heat that year. And if the population also grows to two thousand, then eight heatwave days would create 16,000 person-days of heat.",
                        "values": []
                    },
                    {
                        "template": "Freetown has approximately {{exposure_value}}. Under current climatic conditions,  {{affected_present}} may be exposed to extreme heat events every 100 years. ",
                        "values": [
                            {
                                "key": "exposure_value",
                                "value": 1100000,
                                "units": "people"
                            },
                            {
                                "key": "affected_present",
                                "value": 3374342.477,
                                "units": "person-days"
                            }
                        ]
                    },
                    {
                        "template": "The annual number of person-days of heat is projected to grow by {{future_percent}} to {{future_value}} by 2080 under the middle of the road scenario. This is due both to population change and increasing temperatures. ",
                        "values": [
                            {
                                "key": "future_percent",
                                "value": 151.99573398432482,
                                "units": "%"
                            },
                            {
                                "key": "future_value",
                                "value": 8503197.890041346,
                                "units": "person-days"
                            }
                        ]
                    },
                    {
                        "template": "The climate element of this change is large: in Freetown extreme heat events are projected to increase in frequency by {{frequency_change}} on average by 2080.",
                        "values": [
                            {
                                "key": "frequency_change",
                                "value": 92.99306772452783,
                                "units": "%"
                            }
                        ]
                    },
                    {
                        "template": "The impacts of extreme heat events that would be expected once in 10 years are projected to happen once in {{new_10yr_return}} years instead, and impacts that would be expected once in 100 years are projected to happen once in {{new_100yr_return}} years instead.",
                        "values": [
                            {
                                "key": "new_10yr_return",
                                "value": 2.5421739231899583,
                                "units": "years"
                            },
                            {
                                "key": "new_100yr_return",
                                "value": 16.8857545331257572,
                                "units": "years"
                            }
                        ]
                    }
                ],
                "chart": {
                    "items": [
                        {
                            "year_label": "2020",
                            "year_value": 2020.0,
                            "temperature": null,
                            "current_climate": 3374342.477,
                            "growth_change": 0.0,
                            "climate_change": 0.0,
                            "future_climate": 6512247.06189412,
                            "measure_names": null,
                            "measure_change": null,
                            "measure_climate": null,
                            "combined_measure_change": null,
                            "combined_measure_climate": null
                        },
                        {
                            "year_label": "2040",
                            "year_value": 2040.0,
                            "temperature": null,
                            "current_climate": 3374342.477,
                            "growth_change": 343844.1208764231,
                            "climate_change": 526593.66751636,
                            "future_climate": 4244779.06189412,
                            "measure_names": null,
                            "measure_change": null,
                            "measure_climate": null,
                            "combined_measure_change": null,
                            "combined_measure_climate": null
                        },
                        {
                            "year_label": "2060",
                            "year_value": 2060.0,
                            "temperature": null,
                            "current_climate": 3374342.477,
                            "growth_change": 687688.1208764231,
                            "climate_change": 1053186.66751636,
                            "future_climate": 5115216.06189412,
                            "measure_names": null,
                            "measure_change": null,
                            "measure_climate": null,
                            "combined_measure_change": null,
                            "combined_measure_climate": null
                        },
                        {
                            "year_label": "2080",
                            "year_value": 2080.0,
                            "temperature": null,
                            "current_climate": 3374342.477,
                            "growth_change": 1031533.1208764231,
                            "climate_change": 2106372.66751636,
                            "future_climate": 6512247.06189412,
                            "measure_names": null,
                            "measure_change": null,
                            "measure_climate": null,
                            "combined_measure_change": null,
                            "combined_measure_climate": null
                        }
                    ],
                    "legend": {
                        "title": "Components of extreme_heat risk: 100",
                        "units": "people",
                        "items": [
                            {
                                "label": "Risk today",
                                "slug": "current_climate",
                                "value": null
                            },
                            {
                                "label": "+ growth",
                                "slug": "growth_change",
                                "value": null
                            },
                            {
                                "label": "+ climate change",
                                "slug": "climate_change",
                                "value": null
                            }
                        ]
                    },
                    "units_warming": "degC",
                    "units_response": "people"
                }
            },
            "metadata": {
                "description": "Timeline"
            }
        },
        "response_uri": null,
        "code": null,
        "message": null
    }
    '''
    import json
    result = json.loads(result_json)
    output = schemas_widgets.TimelineWidgetJobSchema(
        job_id=result['job_id'],
        location=location_root + '/' + result['job_id'],
        status="SUCCESS",
        request={},  # TODO work out where to get this from
        completed_at=None,
        expires_at=None,
        response=result['response'],
        response_uri=None,
        code=None,
        message=None
    )
    return output

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
