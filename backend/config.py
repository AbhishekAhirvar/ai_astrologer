import swisseph as swe

# Zodiac Signs
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Sign lords for Vedic astrology
SIGN_LORDS = {
    0: 'Mars',      # Aries
    1: 'Venus',     # Taurus
    2: 'Mercury',   # Gemini
    3: 'Moon',      # Cancer
    4: 'Sun',       # Leo
    5: 'Mercury',   # Virgo
    6: 'Venus',     # Libra
    7: 'Mars',      # Scorpio
    8: 'Jupiter',   # Sagittarius
    9: 'Saturn',    # Capricorn
    10: 'Saturn',   # Aquarius
    11: 'Jupiter'   # Pisces
}

# Natural relationships (Friend=1, Neutral=0, Enemy=-1)
NATURAL_RELATIONSHIPS = {
    'Sun': {'Moon': 1, 'Mars': 1, 'Jupiter': 1, 'Mercury': 0, 'Venus': -1, 'Saturn': -1},
    'Moon': {'Sun': 1, 'Mercury': 1, 'Mars': 0, 'Jupiter': 0, 'Venus': 0, 'Saturn': 0},
    'Mars': {'Sun': 1, 'Moon': 1, 'Jupiter': 1, 'Venus': 0, 'Saturn': 0, 'Mercury': -1},
    'Mercury': {'Sun': 1, 'Venus': 1, 'Mars': 0, 'Jupiter': 0, 'Saturn': 0, 'Moon': -1},
    'Jupiter': {'Sun': 1, 'Moon': 1, 'Mars': 1, 'Mercury': -1, 'Venus': -1, 'Saturn': 0},
    'Venus': {'Mercury': 1, 'Saturn': 1, 'Mars': 0, 'Jupiter': 0, 'Sun': -1, 'Moon': -1},
    'Saturn': {'Venus': 1, 'Mercury': 1, 'Jupiter': 0, 'Sun': -1, 'Moon': -1, 'Mars': -1},
    'Rahu': {'Venus': 1, 'Saturn': 1, 'Mercury': 1, 'Jupiter': 0, 'Sun': -1, 'Moon': -1, 'Mars': -1},
    'Ketu': {'Mars': 1, 'Jupiter': 1, 'Sun': 1, 'Moon': 1, 'Venus': 0, 'Saturn': 0, 'Mercury': -1}
}

# Karaka labels (Atmakaraka to Darakaraka)
KARAKA_LABELS = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']

# Swiss Ephemeris planet IDs
PLANET_IDS = {
    'sun': swe.SUN,
    'moon': swe.MOON,
    'mercury': swe.MERCURY,
    'venus': swe.VENUS,
    'mars': swe.MARS,
    'jupiter': swe.JUPITER,
    'saturn': swe.SATURN,
    'rahu': swe.TRUE_NODE,
}

# Calculation Settings
DEFAULT_AYANAMSA = swe.SIDM_LAHIRI
DEFAULT_HOUSE_SYSTEM = b'P' # Placidus (though we use Whole Sign for chart display, P is often default houses calc in swisseph)
# Actually the code uses Whole Sign manually calculated from Ascendant degree.
# But for `swe.houses` call in `astrology.py`: `houses = swe.houses(jd, lat, lon, b'P')`
