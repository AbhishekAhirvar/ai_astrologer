class AstrologyError(Exception):
    """Base exception for astrology backend."""
    pass

class InvalidDateError(AstrologyError):
    """Raised when date/time input is invalid."""
    pass

class InvalidLocationError(AstrologyError):
    """Raised when latitude/longitude is invalid."""
    pass

class EphemerisCalculationError(AstrologyError):
    """Raised when Swiss Ephemeris calculation fails."""
    pass

class VargaCalculationError(AstrologyError):
    """Raised when divisional chart calculation fails."""
    pass
