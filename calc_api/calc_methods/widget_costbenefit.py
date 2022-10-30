import logging

from calc_api.config import ClimadaCalcApiConfig
from calc_api.vizz import schemas
import calc_api.vizz.models as models

conf = ClimadaCalcApiConfig()

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(getattr(logging, conf.LOG_LEVEL))


def get_default_measures(measure_id: int = None, slug: str = None, hazard_type: str = None, exposure_type: str = None):
    measures = models.Measure.objects.filter(user_generated=False)
    if measure_id:
        measures = measures.filter(id=measure_id)
    if slug:
        measures = measures.filter(slug=slug)
    if hazard_type:
        measures = measures.filter(hazard_type=hazard_type)
    if exposure_type:
        measures = measures.filter(exposure_type=exposure_type)
    return [schemas.MeasureSchema(**m.__dict__) for m in measures]