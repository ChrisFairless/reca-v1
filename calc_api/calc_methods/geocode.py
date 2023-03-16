import requests
import logging
import re
from pycountry import countries

from calc_api.calc_methods.util import country_to_iso

from climada_calc.settings import GEOCODE_URL, MAPTILER_KEY
from calc_api.vizz.schemas_geocoding import GeocodePlaceList, GeocodePlace
from calc_api.calc_methods.util import bbox_to_coords
from calc_api.config import ClimadaCalcApiConfig
from calc_api.vizz.models import Location

conf = ClimadaCalcApiConfig()

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(getattr(logging, conf.LOG_LEVEL))

PRECISION = 6   # Decimal places to round to for lat lon. To avoid rounding errors when calculating hashes
                # from the same input twice. TODO come back to this, we're still at risk of rounding errors


def standardise_location(location_name=None, location_code=None, location_scale=None, location_poly=None):
    if not location_name and not location_code:
        raise ValueError('location data requires location_name or location_code to be properties')

    if location_poly:
        raise ValueError("For now geocoding can't handle polygons. Sorry!")

    if location_scale in ['country', 'admin0']:
        code = country_to_iso(location_name, representation='alpha3')
        return GeocodePlace(
            name=location_name,
            id=location_code if location_code else code,
            scale='country',
            country=location_name,
            country_id=code,
            admin1=None,
            admin1_id=None,
            admin2=None,
            admin2_id=None,
            bbox=None,  # TODO
            poly=None  # TODO
        )
    elif location_scale:
        LOGGER.warning("For now geocoding can't handle location scales other than country: ignoring!")

    # if not location_code and re.search('[\d]{3}', location_name):
    #     LOGGER.warning(f'Looks like location code was provided as location name. Using it as a code: {location_name}')
    #     location_code = location_name

    if location_code:
        return location_from_code(location_code)
    else:
        return location_from_name(location_name)


# TODO cache these results
def location_from_code(location_code):
    if conf.GEOCODER == 'osmnames':
        try:
            return get_one_place(location_code, exact=True)
        except ValueError as msg:
            LOGGER.warning(f'Failed to get an exact match from on the location_code parameter '
                           '{request.location_code}. '
                           'Did you mean to provide a location_name instead? '
                           'Code will try again for a non-exact match. '
                           'Error message: {msg}')

    elif conf.GEOCODER == 'nominatim_web':
        if location_code:
            url = f'https://nominatim.openstreetmap.org/lookup?q=N{location_code}&format=json'
        place = requests.request('GET', url)
        return osmnames_to_schema(place.json())

    # TODO see if maptiler responses are sorted by the 'relevance' property or if we need to do that
    elif conf.GEOCODER == 'maptiler':
        language = 'en'
        url = f'https://api.maptiler.com/geocoding/{location_code}.json?language={language}&key={MAPTILER_KEY}'
        place = requests.get(url=url, headers={'Origin': 'reca-api.herokuapp.com'})  # TODO split this to a setting?
        place = place.json()['features'][0]
        return maptiler_to_schema(place)

    else:
        raise ValueError(f"No valid geocoder selected. Set in climada_calc-config.yaml. Possible values: osmnames, nominatim_web. Current value: {conf.GEOCODER}")


# TODO cache these results
def location_from_name(location_name):
    if conf.GEOCODER == 'osmnames':
        out = get_one_place(location_name, exact=False)

    elif conf.GEOCODER == 'nominatim_web':
        url = f'https://nominatim.openstreetmap.org/search?q={location_name}&format=json'
        place = requests.request('GET', url)
        out = osmnames_to_schema(place.json())

    elif conf.GEOCODER == 'maptiler':
        language = 'en'
        url = f'https://api.maptiler.com/geocoding/{location_name}.json?language={language}&key={MAPTILER_KEY}'
        place = requests.get(url=url, headers={'Origin': 'reca-api.herokuapp.com'})  # TODO move this to a setting?
        place = place.json()['features'][0]
        out = maptiler_to_schema(place)

    else:
        raise ValueError(f"No valid geocoder selected. Set in climada_calc-config.yaml. Possible values: osmnames, nominatim_web. Current value: {conf.GEOCODER}")

    LOGGER.debug(f'Geocoding location with {conf.GEOCODER}.\n    Input: {location_name}\n    Found: {out.name}')
    return out


def osmnames_to_schema(place):
    bbox = [round(x, PRECISION) for x in place['boundingbox']]
    poly = bbox_to_coords(bbox)
    return GeocodePlace(
        name=place['display_name'],
        id=place['osm_id'],
        type=place['type'],
        city=place['city'],
        county=place['county'],
        state=place['state'],
        country=place['country'],
        country_id=country_to_iso(place['country']),
        bbox=bbox,
        poly=poly
    )


def maptiler_to_schema(place):
    try:
        country, country_iso3 = _maptiler_establish_country_from_place(place)
    except ValueError as e:
        # Sometimes when querying by place ID instead of name, we don't get all the relevant information.
        # This fills the gap
        country_details = countries.get(alpha_2=place['properties']['country_code'])
        country, country_iso3 = country_details.name, country_details.alpha_3

    if len(list(place['place_type'])) > 1:
        LOGGER.debug(f'Geocoder was given multiple place types: {place["place_type"]}')

    bbox = [round(x, PRECISION) for x in place['bbox']]
    poly = bbox_to_coords(bbox)

    return GeocodePlace(
        name=place['place_name'],
        id=place['id'],
        scale=place['place_type'][0],
        city=_get_place_context_type(place, 'city'),
        county=_get_place_context_type(place, 'county'),
        state=_get_place_context_type(place, 'state'),
        country=country,
        country_id=country_iso3,
        bbox=bbox,
        poly=poly
    )


def _maptiler_establish_country_from_place(place):
    # TODO implement this for osmschema too
    country = None
    if 'country' in place['place_type']:
        try:
            country = place['place_name']
            country_iso3 = country_to_iso(country)
        except LookupError:
            try:
                country = place['text']
                country_iso3 = country_to_iso(country)
            except LookupError:
                raise LookupError(f'Could not match Maptiler country name to country. '
                                  f'Names tried: {place["place_name"]}, {place["text"]} '
                                  f'\nQuery result:'
                                  f'\n{place}')
    else:
        country = _get_place_context_type(place, 'country')
        if country:
            try:
                country_iso3 = country_to_iso(country)
            except LookupError as e1:
                try:
                    retry_country = country.replace("The ", "")
                    if retry_country != country:
                        country_iso3 = country_to_iso(retry_country)
                    else:
                        raise LookupError(e1)
                except LookupError as e2:
                    raise LookupError(f'Could not match the Maptiler returned country name to a country code. '
                                      f'Country: {country}.'
                                      f'\nError 1: \n{e2}'
                                      f'\nQuery result:'
                                      f'\n{place}')

    if not country:
        raise ValueError(f'No country could be established from this maptiler query:\n{place}')

    return country, country_iso3


def _get_place_context_type(place, placetype):
    if 'context' in place:
        name = [context['text'] for context in place['context'] if placetype in context['id']]
        return None if len(name) == 0 else name[0]
    else:
        return None


def _get_country_from_matching_name(name: str):
    return name.split(',')[-1]


def query_place(s):
    if conf.GEOCODER == 'osmnames':
        query = GEOCODE_URL + "q/" + s
        response = requests.get(query).json()['results']
    elif conf.GEOCODER == 'nominatim_web':
        query = f'https://nominatim.openstreetmap.org/search?q={s}&format=json'
        response = requests.get(query).json()
    elif conf.GEOCODER == 'maptiler':
        language = 'en'
        query = f'https://api.maptiler.com/geocoding/{s}.json?language={language}&key={MAPTILER_KEY}'
        response = requests.get(query, headers={'Origin': 'reca-api.herokuapp.com'}).json()['features']
    else:
        ValueError(
            f"No valid geocoder selected. Set in climada_calc-config.yaml. Possible values: osmnames, nominatim_web. Current value: {conf.GEOCODER}")
    if len(response) == 0:
        return None
    else:
        return response


def get_one_place(s, exact=True):
    db_location = Location.objects.filter(name=s)
    if len(db_location) == 1:
        return GeocodePlaceList(data=[GeocodePlace.from_location_model(db_location[0])])
    db_location = Location.objects.filter(id=s)
    if len(db_location) == 1:
        return GeocodePlaceList(data=[GeocodePlace.from_location_model(db_location[0])])
    response = query_place(s)
    if len(response) == 0:
        raise ValueError(f'Could not identify a place corresponding to {s}')

    if hasattr(response[0], 'display_name'):
        exact_response = [r for r in response if r['display_name'] == s]
    elif hasattr(response[0], 'display_name_en'):
        exact_response = [r for r in response if r['display_name_en'] == s]
    elif hasattr(response[0], 'place_name'):
        exact_response = [r for r in response if r['place_name'] == s]
    else:
        exact_response = [r for r in response if r['id'] == s]

    if exact_response and len(exact_response) > 0:
        answer_is = exact_response[0]
    elif not exact:
        answer_is = response[0]
    else:
        raise ValueError(
            f'Could not exactly identify a place corresponding to {s}. Closest match: {response[0]["display_name"]}')

    if conf.GEOCODER in ['osmnames', 'nominatim_web']:
        return osmnames_to_schema(answer_is)
    elif conf.GEOCODER == 'maptiler':
        return maptiler_to_schema(answer_is)
    else:
        raise ValueError('The config variable GEOCODER must be one of osmnames, nominatim_web, maptiler.')


# TODO make this more resilient to unexpected failures to match
def get_place_hierarchy(s, exact=True):
    place = get_one_place(s, exact)
    if not place:
        return None

    address = place.name.split(', ')
    out = [
        get_one_place(", ".join(address[i:len(address)]), exact=True)
        for i in range(len(address))
    ]
    return GeocodePlaceList(data=out)


# TODO there's no real reason to have this separate from query_place is there?
def geocode_autocomplete(s):
    # TODO fix the location model so this works!!
    db_location = Location.objects.filter(name=s)
    if len(db_location) == 1:
        return GeocodePlaceList(data=[GeocodePlace.from_location_model(db_location[0])])
    db_location = Location.objects.filter(id=s)
    if len(db_location) == 1:
        return GeocodePlaceList(data=[GeocodePlace.from_location_model(db_location[0])])

    response = query_place(s)
    if not response:
        return GeocodePlaceList(data=[])
    if conf.GEOCODER in ['osmnames', 'nominatim_web']:
        suggestions = [osmnames_to_schema(p) for p in response]
    elif conf.GEOCODER == 'maptiler':
        suggestions = [maptiler_to_schema(p) for p in response]
    else:
        raise ValueError('GEOCODE must be one of osmnames, nominatim_web or maptiler')
    return GeocodePlaceList(data=suggestions)


def geocode_precalculated_locations():
    return GeocodePlaceList(data=[GeocodePlace.from_location_model(place) for place in Location.objects.all()])

