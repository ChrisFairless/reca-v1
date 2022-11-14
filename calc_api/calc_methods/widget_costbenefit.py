import logging

from calc_api.config import ClimadaCalcApiConfig
from calc_api.vizz import schemas
import calc_api.vizz.models as models
from calc_api.vizz import units

conf = ClimadaCalcApiConfig()

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(getattr(logging, conf.LOG_LEVEL))


def get_default_measures(
        measure_id: int = None,
        slug: str = None,
        hazard_type: str = None,
        exposure_type: str = None,
        units_hazard: str = None,
        units_currency: str = None,
        units_distance: str = None,
        units_temperature: str = None,
        units_speed: str = None
):

    request = schemas.MeasureRequestSchema(
        measure_id=measure_id,
        slug=slug,
        hazard_type=hazard_type,
        exposure_type=exposure_type,
        units_hazard=units_hazard,
        units_currency=units_currency,
        units_distance=units_distance,
        units_temperature=units_temperature,
        units_speed=units_speed
    )
    request.standardise()

    # TODO: one day we'll want to make this work with any hazard unit type, even unknown ones.
    #  So we'll need to abstract this.
    units_dict = {}
    if request.units_hazard:
        unit_type = units.UNIT_TYPES[request.units_hazard]
        if unit_type == "temperature":
            if request.units_temperature:
                assert units_hazard == request.units_temperature
        elif unit_type == "speed":
            if request.units_speed:
                assert units_hazard == request.units_speed
        else:
            raise ValueError(f'Unexpected hazard unit type. Units: {request.units_hazard}. Type: {unit_type}')
        units_dict[unit_type] = request.units_hazard
    else:
        if request.units_temperature:
            units_dict['temperature'] = request.units_temperature
        if request.units_speed:
            units_dict['speed'] = request.units_speed
    units_dict['currency'] = request.units_currency

    if request.units_distance:
        if request.units_distance != units.NATIVE_UNITS_CLIMADA['distance']:
            raise ValueError("Can't yet convert distance units in measures. Implement!"
                             f"\nRequested: {request.units_distance}"
                             f"\nCLIMADA: {units.NATIVE_UNITS_CLIMADA['distance']}")
    else:
        request.units_distance = units.NATIVE_UNITS_CLIMADA['distance']
    units_dict['distance'] = request.units_distance

    measures = models.Measure.objects.filter(user_generated=False)
    if request.measure_id:
        measures = measures.filter(id=request.measure_id)
    if request.slug:
        measures = measures.filter(slug=request.slug)
    if request.hazard_type:
        measures = measures.filter(hazard_type=request.hazard_type)
    if request.exposure_type:
        measures = measures.filter(exposure_type=request.exposure_type)
    measures_list = [schemas.MeasureSchema(**m.__dict__) for m in measures]
    _ = [measure.convert_units(units_dict) for measure in measures_list]
    return measures_list
