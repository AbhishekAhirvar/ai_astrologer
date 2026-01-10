import unittest
from backend.astrology import generate_vedic_chart
from backend.exceptions import InvalidDateError, InvalidLocationError

class TestAstrologyValidation(unittest.TestCase):
    
    def test_valid_input(self):
        """Test valid input generates a chart."""
        # New Delhi
        chart = generate_vedic_chart("Test User", 2000, 1, 1, 12, 0, "Delhi", 28.7, 77.1)
        # Chart should be ChartResponse object, not error dict
        self.assertNotIsInstance(chart, dict)  # Success returns ChartResponse, not dict
        self.assertIn('sun', chart.planets)
        self.assertIn('ascendant', chart.planets)
        
    def test_invalid_date(self):
        """Test invalid date inputs."""
        # Month 13
        result = generate_vedic_chart("Test", 2000, 13, 1, 12, 0, "City", 20.0, 70.0)
        self.assertIn('error', result)
        # Python's datetime raises "month must be in 1..12"
        self.assertIn('month must be in 1..12', result['error']) 

    def test_invalid_latitude(self):
        """Test invalid latitude."""
        result = generate_vedic_chart("Test", 2000, 1, 1, 12, 0, "City", 95.0, 70.0)
        self.assertIn('error', result)
        self.assertIn('Latitude must be between', result['error'])
        
    def test_invalid_longitude(self):
        """Test invalid longitude."""
        result = generate_vedic_chart("Test", 2000, 1, 1, 12, 0, "City", 20.0, 190.0)
        self.assertIn('error', result)
        self.assertIn('Longitude must be between', result['error'])

if __name__ == '__main__':
    unittest.main()
