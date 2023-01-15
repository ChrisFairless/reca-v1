import logging
from shapely.geometry import Polygon
from shapely import wkt
import numpy as np
import pycountry
import re

from calc_api.config import ClimadaCalcApiConfig
from calc_api.vizz.enums import SCENARIO_LOOKUPS

conf = ClimadaCalcApiConfig()

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(getattr(logging, conf.LOG_LEVEL))


# TODO probably make this a class
def standardise_scenario(scenario_name=None, scenario_growth=None, scenario_climate=None, scenario_year=None):

    if not scenario_name and (scenario_climate is None or scenario_growth is None):
        raise ValueError('When scenario_name is not set, scenario_climate and scenario_growth must be')

    if scenario_year and int(scenario_year) == 2020:
        return 'historical', 'historical', 'historical'

    if scenario_name and not scenario_growth:
        scenario_growth = SCENARIO_LOOKUPS[scenario_name]['scenario_growth']
    if scenario_name and not scenario_climate:
        scenario_climate = SCENARIO_LOOKUPS[scenario_name]['scenario_climate']

    return scenario_name, scenario_growth, scenario_climate


def convert_to_polygon(location_poly):
    if isinstance(location_poly, list):
        if isinstance(location_poly[0], list):
            location_poly = Polygon(location_poly)
        else:
            if len(location_poly) != 4:
                raise ValueError(f'Could not read location polygon: {location_poly}')
            else:
                location_poly = bbox_to_wkt(location_poly)
    if isinstance(location_poly, str):
        location_poly = wkt.loads(location_poly)
    if len(location_poly.exterior.coords[:]) - 1 != 4:
        LOGGER.warning("API doesn't handle non-bounding box polygons yet: converting to box")
    return location_poly


def bbox_to_poly(bbox):
    if len(bbox) != 4:
        raise ValueError('Expected bbox to have four points')
    # TODO use climada utils to standardise around 180 degrees longitude
    lat_list = [bbox[i] for i in [1, 3, 3, 1]]
    lon_list = [bbox[i] for i in [0, 0, 2, 2]]
    return Polygon([[lon, lat] for lat, lon in zip(lat_list, lon_list)])


def poly_to_coords(poly):
    return [list(coord) for coord in poly.exterior.coords]


def bbox_to_coords(bbox):
    return poly_to_coords(bbox_to_poly(bbox))


def bbox_to_wkt(bbox):
    return bbox_to_poly(bbox).wkt


# STOLEN from climada.util.coordinates so I don't have to import CLIMADA for this
def country_to_iso(countries, representation="alpha3", fillvalue=None):
    """Determine ISO 3166 representation of countries

    Example
    -------
    >>> country_to_iso(840)
    'USA'
    >>> country_to_iso("United States", representation="alpha2")
    'US'
    >>> country_to_iso(["United States of America", "SU"], "numeric")
    [840, 810]

    Some geopolitical areas that are not covered by ISO 3166 are added in the "user-assigned"
    range of ISO 3166-compliant values:

    >>> country_to_iso(["XK", "Dhekelia"], "numeric")  # XK for Kosovo
    [983, 907]

    Parameters
    ----------
    countries : one of str, int, list of str, list of int
        Country identifiers: name, official name, alpha-2, alpha-3 or numeric ISO codes.
        Numeric representations may be specified as str or int.
    representation : str (one of "alpha3", "alpha2", "numeric", "name"), optional
        All countries are converted to this representation according to ISO 3166.
        Default: "alpha3".
    fillvalue : str or int or None, optional
        The value to assign if a country is not recognized by the given identifier. By default,
        a LookupError is raised. Default: None

    Returns
    -------
    iso_list : one of str, int, list of str, list of int
        ISO 3166 representation of countries. Will only return a list if the input is a list.
        Numeric representations are returned as integers.
    """
    return_single = np.isscalar(countries)
    countries = [countries] if return_single else countries

    if not re.match(r"(alpha[-_]?[23]|numeric|name)", representation):
        raise ValueError(f"Unknown ISO representation: {representation}")
    representation = re.sub(r"alpha-?([23])", r"alpha_\1", representation)

    iso_list = []
    for country in countries:
        country = country if isinstance(country, str) else f"{int(country):03d}"
        try:
            match = pycountry.countries.lookup(country)
        except LookupError:
            try:
                match = pycountry.historic_countries.lookup(country)
            except LookupError:
                match = next(filter(lambda c: country in c.values(), NONISO_REGIONS), None)
                if match is not None:
                    match = pycountry.db.Data(**match)
                elif fillvalue is not None:
                    match = pycountry.db.Data(**{representation: fillvalue})
                else:
                    raise LookupError(f'Unknown country identifier: {country}') from None
        iso = getattr(match, representation)
        if representation == "numeric":
            iso = int(iso)
        iso_list.append(iso)
    return iso_list[0] if return_single else iso_list

