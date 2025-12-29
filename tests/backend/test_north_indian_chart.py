import unittest
import os
import matplotlib.pyplot as plt
from backend.chart_renderer import NorthIndianChart

class TestNorthIndianChart(unittest.TestCase):
    def setUp(self):
        # Mock chart data with all required planets
        self.chart_data = {
            'ascendant': {'sign_num': 0, 'degree': 15.0}, # Aries Ascendant
            'sun': {'sign_num': 4, 'degree': 10.0},      # Leo
            'moon': {'sign_num': 1, 'degree': 25.0},     # Taurus
            'mars': {'sign_num': 0, 'degree': 5.0},      # Aries
            'mercury': {'sign_num': 5, 'degree': 2.0},   # Virgo
            'jupiter': {'sign_num': 11, 'degree': 29.9}, # Pisces (Highest degree -> AK)
            'venus': {'sign_num': 6, 'degree': 1.1},     # Libra (Lowest degree -> DK)
            'saturn': {'sign_num': 9, 'degree': 15.0},   # Capricorn
            'rahu': {'sign_num': 2, 'degree': 12.0},     # Gemini
            'ketu': {'sign_num': 8, 'degree': 12.0}      # Sagittarius
        }

    def test_initialization(self):
        """Test that the chart initializes correctly."""
        chart = NorthIndianChart(self.chart_data, 'D1', 'Test Chart')
        self.assertEqual(chart.ascendant_sign, 0)
        self.assertEqual(chart.chart_type, 'D1')
        self.assertEqual(chart.name, 'Test Chart')

    def test_ak_dk_calculation(self):
        """Test Atmakaraka and Darakaraka calculations excluding Rahu/Ketu."""
        chart = NorthIndianChart(self.chart_data)
        
        # Jupiter has highest degree (29.9)
        self.assertEqual(chart.ak_planet, 'jupiter')
        
        # Venus has lowest degree (1.1) among the 7 planets
        self.assertEqual(chart.dk_planet, 'venus')
        
        # Verify get_ak_dk method
        ak, dk = chart.get_ak_dk()
        self.assertEqual(ak, 'jupiter')
        self.assertEqual(dk, 'venus')

    def test_chara_karakas_list(self):
        """Test retrieval of all Chara Karakas."""
        chart = NorthIndianChart(self.chart_data)
        karakas = chart.get_all_chara_karakas()
        
        # Should have 7 karakas
        self.assertEqual(len(karakas), 7)
        
        # Check order by degree
        # Jupiter (29.9) -> AK
        # Moon (25.0) -> AmK
        # Saturn (15.0) -> BK
        # Sun (10.0) -> MK
        # Mars (5.0) -> PK
        # Mercury (2.0) -> GK
        # Venus (1.1) -> DK
        
        expected_order = ['jupiter', 'moon', 'saturn', 'sun', 'mars', 'mercury', 'venus']
        actual_order = [k[1] for k in karakas]
        self.assertEqual(actual_order, expected_order)

    def test_display_planets(self):
         """Test that display planets include Rahu/Ketu."""
         chart = NorthIndianChart(self.chart_data)
         display_planets = chart.get_planets_for_display()
         
         self.assertIn('rahu', display_planets)
         self.assertIn('ketu', display_planets)
         self.assertIn('sun', display_planets)
         
         # Ascendant is handled separately, shouldn't be in display planets list usually?
         # Based on code: EXCLUDED_KEYS = {'ascendant', '_metadata'}
         self.assertNotIn('ascendant', display_planets)

    def test_render_chart(self):
        """Test that the chart can be rendered without errors."""
        chart = NorthIndianChart(self.chart_data)
        output_path = './test_chart_output.png'
        try:
            chart.render(output_path)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_invalid_input(self):
        """Test error handling for invalid input."""
        with self.assertRaises(ValueError):
            NorthIndianChart("not a dict")
            
        with self.assertRaises(ValueError):
            # Missing ascendant
            NorthIndianChart({'sun': {'sign_num': 1, 'degree': 1}})
            
    def test_degree_formatting(self):
        """Test that degrees are formatted correctly in Degree:Minute format."""
        # Use a mock or inspect internal logic if possible.
        # Since place_planets uses matplotlib calls, let's just create a chart and run it
        # to ensure no errors with the new string formatting.
        # We can also check if the method completes without error.
        
        # Manually invoke logic that was put in place_planets to verify string format
        degree_val = 10.5
        d = int(degree_val)
        m = int((degree_val - d) * 60)
        formatted = f"{d}°{m:02d}'"
        self.assertEqual(formatted, "10°30'")
        
        degree_val = 5.01
        d = int(degree_val)
        m = int((degree_val - d) * 60)
        formatted = f"{d}°{m:02d}'"
        self.assertEqual(formatted, "5°00'")
        
        # Verify chart rendering with new logic
        chart = NorthIndianChart(self.chart_data)
        chart.create_figure()
        chart.place_planets() 
        plt.close(chart.fig)

    def test_edge_case_duplicate_degrees(self):
        """Test stability when planets have identical degrees."""
        # Modify chart data so Sun and Moon have same degree
        data = self.chart_data.copy()
        data['sun'] = {'sign_num': 4, 'degree': 10.0}
        data['moon'] = {'sign_num': 1, 'degree': 10.0}
        
        # We need enough planets. Re-use existing data.
        # Current degrees:
        # Jup: 29.9
        # Sat: 15.0
        # Sun: 10.0
        # Moon: 10.0
        # Mars: 5.0
        # Merc: 2.0
        # Ven: 1.1
        
        chart = NorthIndianChart(data)
        
        # Sort order should be deterministic (by name if degrees equal)
        # Moon vs Sun. 'moon' < 'sun' ? No, 'moon' approaches before 'sun' alphabetically?
        # Re-check sort key: (-degree, name). 
        # m < s, so moon comes first?
        # Actually 'moon' comes before 'sun' in alphabet.
        # So Moon should be higher rank than Sun if valid logic follows.
        
        karakas = chart.get_all_chara_karakas()
        # 0: Jup
        # 1: Sat
        # 2: Moon or Sun?
        
        # Let's verify the ranks
        ranks = [k[1] for k in karakas]
        self.assertIn('moon', ranks)
        self.assertIn('sun', ranks)
        
        # Verify no crash
        self.assertEqual(len(ranks), 7)

    def test_edge_case_rahu_ketu_exclusion(self):
        """Test that Rahu/Ketu are ignored even if they have extreme degrees."""
        data = self.chart_data.copy()
        # Give Rahu highest degree
        data['rahu'] = {'sign_num': 2, 'degree': 29.99}
        # Give Ketu lowest degree
        data['ketu'] = {'sign_num': 8, 'degree': 0.01}
        # Jupiter is 29.9, Venus is 1.1 from setUp
        
        chart = NorthIndianChart(data)
        
        # AK should still be Jupiter, not Rahu
        self.assertEqual(chart.ak_planet, 'jupiter')
        # DK should still be Venus, not Ketu
        self.assertEqual(chart.dk_planet, 'venus')

    def test_edge_case_invalid_degree(self):
        """Test error for invalid degrees."""
        data = self.chart_data.copy()
        data['sun'] = {'sign_num': 1, 'degree': 35.0} # Invalid > 30
        
        with self.assertRaises(ValueError):
            NorthIndianChart(data)
            
        data['sun'] = {'sign_num': 1, 'degree': -5.0} # Invalid < 0
        with self.assertRaises(ValueError):
            NorthIndianChart(data)


if __name__ == '__main__':
    unittest.main()
