import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import numpy as np
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

PLANET_NAMES = {
    'sun': 'Sun',
    'moon': 'Moon',
    'mercury': 'Mercury',
    'venus': 'Venus',
    'mars': 'Mars',
    'jupiter': 'Jupiter',
    'saturn': 'Saturn',
    'rahu': 'Rahu',
    'ketu': 'Ketu',
    'ascendant': 'Asc'
}

# Rashi names (optional for display)
RASHI_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]


class NorthIndianChart:
    """North Indian Chart - Industry Standard"""
    
    def __init__(self, chart_data, chart_type='D1', name=''):
        self.chart_data = chart_data
        self.chart_type = chart_type
        self.name = name
        self.fig = None
        self.ax = None
        
        # Get ascendant sign number (0-11)
        if chart_type == 'D1':
            self.ascendant_sign = chart_data.get('ascendant', {}).get('sign_num', 0)
        else:
            div_chart = chart_data.get(f'{chart_type.lower()}_chart', {})
            self.ascendant_sign = div_chart.get('ascendant', {}).get('sign_num', 0)
        
        self.ak_planet = None
        self.dk_planet = None
        self._calculate_ak_dk()
    
    def _calculate_ak_dk(self):
        """Calculate AK/DK based on degrees within sign"""
        if self.chart_type == 'D1':
            data = self.chart_data
        else:
            data = self.chart_data.get(f'{self.chart_type.lower()}_chart', {})
        
        planet_degrees = []
        for planet_key, planet_data in data.items():
            if planet_key in ['rahu', 'ketu', 'ascendant', '_metadata',
                            'd9_chart', 'd10_chart', 'd12_chart']:
                continue
            if not isinstance(planet_data, dict):
                continue
            
            degree = planet_data.get('degree', 0)
            planet_degrees.append((planet_key, degree))
        
        # Sort by degree within sign (descending)
        planet_degrees.sort(key=lambda x: x[1], reverse=True)
        
        if len(planet_degrees) >= 1:
            self.ak_planet = planet_degrees[0][0]
        if len(planet_degrees) >= 7:
            self.dk_planet = planet_degrees[6][0]
    
    def create_figure(self):
        """Create figure with better resolution"""
        self.fig, self.ax = plt.subplots(figsize=(11, 11), dpi=200)
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 10)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.fig.patch.set_facecolor('white')
        self.ax.set_facecolor('white')
    
    def draw_structure(self):
        """Draw chart structure"""
        # Outer square - slightly thicker
        outer = Rectangle((1, 1), 8, 8, fill=False,
                         edgecolor='black', linewidth=3.0)
        self.ax.add_patch(outer)
        
        # Diamond midpoints
        left_mid = (1, 5)
        top_mid = (5, 9)
        right_mid = (9, 5)
        bottom_mid = (5, 1)
        
        # Inner diamond
        diamond_x = [left_mid[0], top_mid[0], right_mid[0], bottom_mid[0], left_mid[0]]
        diamond_y = [left_mid[1], top_mid[1], right_mid[1], bottom_mid[1], left_mid[1]]
        self.ax.plot(diamond_x, diamond_y, 'k-', linewidth=3.0)
        
        # Diagonals
        self.ax.plot([1, 9], [1, 9], 'k-', linewidth=3.0)
        self.ax.plot([1, 9], [9, 1], 'k-', linewidth=3.0)
    
    def get_house_data(self):
        """
        House positions optimized for rashi number display
        Industry standard positioning
        """
        houses = {
            # House 1: Top triangle (Ascendant position)
            1: {
                'text_center': (5, 7.0),
                'rashi_pos': (5, 8.5),      # Prominent top position
                'font_size': 9
            },
            # House 2: Top-left small triangle
            2: {
                'text_center': (2.8, 7.8),
                'rashi_pos': (1.7, 8.5),    # Top-left corner
                'font_size': 8
            },
            # House 3: Left-upper
            3: {
                'text_center': (1.8, 6.5),
                'rashi_pos': (1.3, 7.5),    # Left upper
                'font_size': 8
            },
            # House 4: Left big triangle
            4: {
                'text_center': (2.2, 5.0),
                'rashi_pos': (1.3, 5.0),    # Left center
                'font_size': 9
            },
            # House 5: Left-lower
            5: {
                'text_center': (1.8, 3.5),
                'rashi_pos': (1.3, 2.5),    # Left lower
                'font_size': 8
            },
            # House 6: Bottom-left small
            6: {
                'text_center': (2.8, 2.2),
                'rashi_pos': (1.7, 1.5),    # Bottom-left corner
                'font_size': 8
            },
            # House 7: Bottom triangle
            7: {
                'text_center': (5, 3.0),
                'rashi_pos': (5, 1.5),      # Bottom center
                'font_size': 9
            },
            # House 8: Bottom-right small
            8: {
                'text_center': (7.2, 2.2),
                'rashi_pos': (8.3, 1.5),    # Bottom-right corner
                'font_size': 8
            },
            # House 9: Right-lower
            9: {
                'text_center': (8.2, 3.5),
                'rashi_pos': (8.7, 2.5),    # Right lower
                'font_size': 8
            },
            # House 10: Right big triangle
            10: {
                'text_center': (7.8, 5.0),
                'rashi_pos': (8.7, 5.0),    # Right center
                'font_size': 9
            },
            # House 11: Right-upper
            11: {
                'text_center': (8.2, 6.5),
                'rashi_pos': (8.7, 7.5),    # Right upper
                'font_size': 8
            },
            # House 12: Top-right small
            12: {
                'text_center': (7.2, 7.8),
                'rashi_pos': (8.3, 8.5),    # Top-right corner
                'font_size': 8
            },
        }
        
        return houses
    
    def place_house_numbers(self):
        """
        Place RASHI numbers (1-12) in corners
        Industry standard: Clear, bold, easily readable
        """
        houses = self.get_house_data()
        
        for house_num in range(1, 13):
            house_data = houses[house_num]
            rashi_pos = house_data['rashi_pos']
            
            # Calculate which RASHI is in this house
            # House 1 contains ascendant_sign, House 2 contains next sign, etc.
            rashi_sign_num = (self.ascendant_sign + house_num - 1) % 12
            rashi_number = rashi_sign_num + 1  # Convert to 1-12
            
            # Display rashi number prominently
            self.ax.text(
                rashi_pos[0], rashi_pos[1], 
                str(rashi_number),
                ha='center', va='center',
                fontsize=11,           # Larger size
                color='#2E4057',       # Dark blue-grey (professional)
                weight='bold',         # Bold for visibility
                family='sans-serif',
                bbox=dict(boxstyle='circle,pad=0.2', 
                         facecolor='#FFFFFF',    # White background
                         edgecolor='#2E4057', 
                         linewidth=1.2,
                         alpha=0.8)
            )
    
    def get_planets_by_house(self):
        """Group planets by house"""
        if self.chart_type == 'D1':
            data = self.chart_data
        else:
            data = self.chart_data.get(f'{self.chart_type.lower()}_chart', {})
        
        planets_in_houses = {i: [] for i in range(1, 13)}
        
        for planet_key, planet_data in data.items():
            if planet_key in ['_metadata', 'd9_chart', 'd10_chart', 'd12_chart']:
                continue
            if not isinstance(planet_data, dict):
                continue
            
            sign_num = planet_data.get('sign_num', 0)
            degree = planet_data.get('degree', 0)
            
            # Calculate house number from sign
            house_num = ((sign_num - self.ascendant_sign) % 12) + 1
            
            planet_name = PLANET_NAMES.get(planet_key, planet_key[:3])
            
            prefix = ''
            if planet_key == self.ak_planet:
                prefix = 'AK '
            elif planet_key == self.dk_planet:
                prefix = 'DK '
            
            planets_in_houses[house_num].append({
                'name': planet_name,
                'degree': degree,
                'prefix': prefix
            })
        
        return planets_in_houses
    
    def place_planets(self):
        """Place planets with better formatting"""
        houses = self.get_house_data()
        planets_by_house = self.get_planets_by_house()
        
        for house_num, planets in planets_by_house.items():
            if not planets:
                continue
            
            house_data = houses[house_num]
            center_pos = house_data['text_center']
            font_size = house_data['font_size']
            
            # Adjust spacing based on number of planets
            num_planets = len(planets)
            if num_planets > 3:
                font_size = max(font_size - 1, 7)
                line_height = 0.26
            else:
                line_height = 0.32
            
            # Vertical distribution
            if num_planets == 1:
                start_y = center_pos[1]
            else:
                total_height = (num_planets - 1) * line_height
                start_y = center_pos[1] + (total_height / 2)
            
            # Place each planet
            for idx, planet in enumerate(planets):
                y_pos = start_y - (idx * line_height)
                
                prefix = planet['prefix']
                name = planet['name']
                degree = planet['degree']
                
                text = f"{prefix}{name} {degree:.0f}°"
                
                # Truncate if too long
                if len(text) > 15:
                    text = text[:14] + '°'
                
                self.ax.text(
                    center_pos[0], y_pos, text,
                    ha='center', va='center',
                    fontsize=font_size,
                    color='#1a1a1a',      # Dark text
                    weight='medium',
                    family='sans-serif'
                )
    
    def add_title(self):
        """Add title with chart type"""
        titles = {
            'D1': 'Rasi (Birth) Chart',
            'D9': 'Navamsa Chart (D9)',
            'D10': 'Dasamsa Chart (D10)',
            'D12': 'Dwadasamsa Chart (D12)'
        }
        
        title = titles.get(self.chart_type, 'Chart')
        if self.name:
            title = f"{title} - {self.name}"
        
        # Add ascendant info
        asc_rashi = RASHI_NAMES[self.ascendant_sign]
        subtitle = f"Ascendant: {asc_rashi}"
        
        self.ax.text(
            5, 9.7, title,
            ha='center', va='bottom',
            fontsize=13, weight='bold',
            color='#1a1a1a',
            family='sans-serif'
        )
        
        self.ax.text(
            5, 0.3, subtitle,
            ha='center', va='top',
            fontsize=9, weight='normal',
            color='#555555',
            family='sans-serif'
        )
    
    def render(self, output_path):
        """Render chart to file"""
        self.create_figure()
        self.draw_structure()
        self.place_house_numbers()  # This now places RASHI numbers
        self.place_planets()
        self.add_title()
        
        self.fig.savefig(
            output_path,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none',
            dpi=200,
            pad_inches=0.4
        )
        plt.close(self.fig)
        return output_path


class NakshatraTable:
    """Nakshatra information table"""
    
    def __init__(self, nakshatra_info):
        self.nakshatra_info = nakshatra_info
    
    def render(self, output_path):
        """Render nakshatra table as image"""
        width, height = 900, 1200
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        y = 50
        title = f"Moon Nakshatra: {self.nakshatra_info.get('nakshatra', 'N/A')}"
        draw.text((40, y), title, fill='#1a1a1a', font=title_font)
        y += 70
        
        symbol_raw = self.nakshatra_info.get('symbol', 'N/A')
        symbol_clean = "".join(c for c in symbol_raw if ord(c) < 128 or c.isalnum() or c.isspace()).strip()
        
        details = [
            f"Number: {self.nakshatra_info.get('number', 'N/A')}/27",
            f"Lord: {self.nakshatra_info.get('lord', 'N/A')}",
            f"Pada: {self.nakshatra_info.get('pada', 'N/A')}/4",
            f"Element: {self.nakshatra_info.get('element', 'N/A')}",
            f"Symbol: {symbol_clean}",
            f"Deity: {self.nakshatra_info.get('deity', 'N/A')}",
        ]
        
        for detail in details:
            draw.text((60, y), detail, fill='#1a1a1a', font=text_font)
            y += 40
        
        img.save(output_path)
        return output_path


def generate_all_charts(chart_data, person_name='', output_dir='./generated_charts'):
    """Generate all divisional charts"""
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for chart_type in ['D1', 'D9', 'D10', 'D12']:
        try:
            renderer = NorthIndianChart(chart_data, chart_type, person_name)
            output_path = f"{output_dir}/{person_name}_{chart_type}_{timestamp}.png"
            renderer.render(output_path)
            results[chart_type] = output_path
            print(f"✓ {chart_type} chart generated: {output_path}")
        except Exception as e:
            print(f"✗ Error generating {chart_type}: {e}")
            results[chart_type] = None
    
    # Generate nakshatra table
    try:
        moon_naks = chart_data.get('moon', {}).get('nakshatra', {})
        if moon_naks:
            nak_renderer = NakshatraTable(moon_naks)
            nak_path = f"{output_dir}/{person_name}_Nakshatra_{timestamp}.png"
            nak_renderer.render(nak_path)
            results['nakshatra'] = nak_path
            print(f"✓ Nakshatra table generated: {nak_path}")
    except Exception as e:
        print(f"✗ Error generating nakshatra table: {e}")
        results['nakshatra'] = None
    
    return results