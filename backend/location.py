from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

def get_location_data(place_name):
    """
    Returns (latitude, longitude, address) for a given place name.
    Returns None if not found or error.
    """
    geolocator = Nominatim(user_agent="astro_chatbot_mvp")
    try:
        location = geolocator.geocode(place_name)
        if location:
            return location.latitude, location.longitude, location.address
        else:
            return None
    except (GeocoderTimedOut, GeocoderUnavailable):
        return None
