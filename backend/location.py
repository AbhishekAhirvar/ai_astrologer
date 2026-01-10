import asyncio
from functools import lru_cache
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from backend.logger import logger

@lru_cache(maxsize=500)
def _sync_geocoding_lookup(place_name: str):
    """Synchronous cached geocoding lookup."""
    geolocator = Nominatim(user_agent="astro_chatbot_mvp")
    return geolocator.geocode(place_name)

async def get_location_data(place_name):
    """
    Returns (latitude, longitude, address) for a given place name.
    Returns None if not found or error.
    """
    try:
        logger.info(f"Looking up location: {place_name}")
        location = await asyncio.to_thread(_sync_geocoding_lookup, place_name)
        if location:
            return location.latitude, location.longitude, location.address
        else:
            return None
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        logger.error(f"Geocoding service error: {str(e)}")
        return None
