import asyncio
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from backend.logger import logger

async def get_location_data(place_name):
    """
    Returns (latitude, longitude, address) for a given place name.
    Returns None if not found or error.
    """
    def sync_lookup():
        geolocator = Nominatim(user_agent="astro_chatbot_mvp")
        return geolocator.geocode(place_name)

    try:
        logger.info(f"Looking up location: {place_name}")
        location = await asyncio.to_thread(sync_lookup)
        if location:
            return location.latitude, location.longitude, location.address
        else:
            return None
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        logger.error(f"Geocoding service error: {str(e)}")
        return None
