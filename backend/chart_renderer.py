import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import numpy as np
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Optional, Tuple

# Rashi names (optional for display)
RASHI_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]


class NorthIndianChart:
    """North Indian Chart - Industry Standard for Vedic Astrology"""
    
    # Constants
    # Constants
    CHART_SIZE = 10
    OUTER_MARGIN = 1
    INNER_SIZE = 8
    LINE_WIDTH_OUTER = 3.0
    LINE_WIDTH_INNER = 3.0
    FIGURE_SIZE = (11, 11)
    DPI = 200
    
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

    # Valid planets for Chara Karaka calculation (7 planets only)
    CHARA_KARAKA_PLANETS = {'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn'}
    
    # All planets for display (including Rahu/Ketu)
    DISPLAY_PLANETS = {'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu'}
    
    EXCLUDED_KEYS = {'ascendant', '_metadata'}
    
    def __init__(self, chart_data: Dict[str, Any], chart_type: str = 'D1', name: str = '') -> None:
        """
        Initialize North Indian Chart
        
        Args:
            chart_data: Dictionary containing planetary positions with structure:
                       {
                           'planet_name': {'sign_num': int, 'degree': float},
                           'ascendant': {'sign_num': int},
                           'rahu': {'sign_num': int, 'degree': float},
                           'ketu': {'sign_num': int, 'degree': float},
                           ...
                       }
            chart_type: Chart type - 'D1' (Rashi), 'D9' (Navamsa), etc.
            name: Optional name/title for the chart
        """
        if hasattr(chart_data, 'dict'):
            # Convert Pydantic model to dict for internal usage
            self.chart_data = chart_data.dict()
            # If ChartResponse structure (planets + vargas flattened for this renderer?)
            # The renderer expects D1 data at top level OR proper keys.
            # ChartResponse has 'planets' and 'vargas'.
            # NorthIndianChart logic expects flat dict with planets AND keys like 'd9_chart'.
            # We need to flatten it if it matches ChartResponse structure.
            if 'planets' in self.chart_data and 'vargas' in self.chart_data:
                # Flask flatten for renderer compatibility
                flat_data = self.chart_data['planets'].copy()
                flat_data.update(self.chart_data['vargas'])
                flat_data['_metadata'] = self.chart_data.get('metadata', {})
                self.chart_data = flat_data
        elif isinstance(chart_data, dict):
            self.chart_data = chart_data
        else:
            # Try vars() or fail
            try:
                self.chart_data = vars(chart_data)
            except:
                raise ValueError("chart_data must be a dictionary or Pydantic model")
        self.chart_type = chart_type.upper()
        self.name = name
        self.fig: Optional[plt.Figure] = None
        self.ax: Optional[plt.Axes] = None
        
        # Get ascendant sign number (0-11)
        ascendant_data = self._get_active_chart_data()
        if 'ascendant' not in ascendant_data:
            raise ValueError("Chart data must contain 'ascendant' key")
            
        self.ascendant_sign = ascendant_data.get('ascendant', {}).get('sign_num', 0)
        self._validate_sign_num(self.ascendant_sign)
        
        self.ak_planet: Optional[str] = None
        self.dk_planet: Optional[str] = None
        self._calculate_ak_dk()
    
    def _get_active_chart_data(self) -> Dict[str, Any]:
        """Get the active chart data based on chart type"""
        if self.chart_type == 'D1':
            return self.chart_data
        else:
            chart_key = f'{self.chart_type.lower()}_chart'
            if chart_key not in self.chart_data:
                raise ValueError(f"Chart data does not contain '{chart_key}'")
            return self.chart_data[chart_key]
    
    @staticmethod
    def _validate_sign_num(sign_num: int) -> None:
        """Validate sign number is in valid range (0-11)"""
        if not isinstance(sign_num, int) or not (0 <= sign_num <= 11):
            raise ValueError(f"sign_num must be integer between 0-11, got {sign_num}")

    def _calculate_ak_dk(self) -> None:
        """
        Calculate Atmakaraka (AK) and Darakaraka (DK) based on degrees within sign
        
        Chara Karakas in descending order of degrees:
        1. AK (Atmakaraka) - Highest degree
        2. AmK (Amatyakaraka)
        3. BK (Bhratrukaraka)
        4. MK (Matrukaraka)
        5. PK (Putrakaraka)
        6. GK (Gnatikaraka)
        7. DK (Darakaraka) - Lowest degree
        
        Note: Rahu and Ketu are EXCLUDED from Chara Karaka calculations
        """
        data = self._get_active_chart_data()
        
        planet_degrees: List[Tuple[str, float]] = []
        
        for planet_key, planet_data in data.items():
            # Skip non-planet keys
            if planet_key in self.EXCLUDED_KEYS:
                continue
            
            # Skip divisional chart keys (d9_chart, d10_chart, etc.)
            if planet_key.startswith('d') and '_chart' in planet_key:
                continue
            
            if not isinstance(planet_data, dict):
                continue
            
            # Only include the 7 planets for Chara Karaka (exclude Rahu/Ketu)
            if planet_key.lower() not in self.CHARA_KARAKA_PLANETS:
                continue
            
            degree = planet_data.get('degree')
            if degree is None:
                raise ValueError(f"Planet '{planet_key}' missing 'degree' key")
            
            if not isinstance(degree, (int, float)) or not (0 <= degree < 30):
                raise ValueError(f"Invalid degree {degree} for planet '{planet_key}' (must be 0-30)")
            
            planet_degrees.append((planet_key, float(degree)))
        
        if len(planet_degrees) < 7:
            raise ValueError(
                f"Need exactly 7 planets for AK/DK calculation, found {len(planet_degrees)}: "
                f"{[p[0] for p in planet_degrees]}"
            )
        
        # Sort by degree within sign (descending), then by name for stability
        planet_degrees.sort(key=lambda x: (-x[1], x[0]))
        
        # AK is highest degree (index 0)
        self.ak_planet = planet_degrees[0][0]
        
        # DK is lowest degree (index 6, which is last of 7 planets)
        self.dk_planet = planet_degrees[6][0]

    def get_planets_for_display(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all planets for chart rendering including Rahu and Ketu
        
        Returns:
            Dictionary of planets to display with their data
        """
        data = self._get_active_chart_data()
        display_planets = {}
        
        for planet_key, planet_data in data.items():
            # Skip non-planet keys
            if planet_key in self.EXCLUDED_KEYS:
                continue
            
            # Skip divisional chart keys
            if planet_key.startswith('d') and '_chart' in planet_key:
                continue
            
            if not isinstance(planet_data, dict):
                continue
            
            # Include all display planets (7 planets + Rahu + Ketu)
            if planet_key.lower() in self.DISPLAY_PLANETS:
                display_planets[planet_key] = planet_data
        
        return display_planets
    
    def create_figure(self) -> None:
        """Create figure with high resolution for clear rendering"""
        self.fig, self.ax = plt.subplots(
            figsize=self.FIGURE_SIZE, 
            dpi=self.DPI
        )
        self.ax.set_xlim(0, self.CHART_SIZE)
        self.ax.set_ylim(0, self.CHART_SIZE)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.fig.patch.set_facecolor('white')
        self.ax.set_facecolor('white')
    
    def draw_structure(self) -> None:
        """Draw North Indian chart structure (diamond within square)"""
        if self.ax is None:
            raise RuntimeError("Must call create_figure() before draw_structure()")
        
        # Outer square
        outer = Rectangle(
            (self.OUTER_MARGIN, self.OUTER_MARGIN), 
            self.INNER_SIZE, 
            self.INNER_SIZE, 
            fill=False,
            edgecolor='black', 
            linewidth=self.LINE_WIDTH_OUTER
        )
        self.ax.add_patch(outer)
        
        # Diamond midpoints
        center = self.OUTER_MARGIN + self.INNER_SIZE / 2
        
        left_mid = (self.OUTER_MARGIN, center)
        top_mid = (center, self.OUTER_MARGIN + self.INNER_SIZE)
        right_mid = (self.OUTER_MARGIN + self.INNER_SIZE, center)
        bottom_mid = (center, self.OUTER_MARGIN)
        
        # Inner diamond
        diamond_x = [left_mid[0], top_mid[0], right_mid[0], bottom_mid[0], left_mid[0]]
        diamond_y = [left_mid[1], top_mid[1], right_mid[1], bottom_mid[1], left_mid[1]]
        self.ax.plot(diamond_x, diamond_y, 'k-', linewidth=self.LINE_WIDTH_INNER)
        
        # Diagonals
        max_coord = self.OUTER_MARGIN + self.INNER_SIZE
        self.ax.plot(
            [self.OUTER_MARGIN, max_coord], 
            [self.OUTER_MARGIN, max_coord], 
            'k-', 
            linewidth=self.LINE_WIDTH_INNER
        )
        self.ax.plot(
            [self.OUTER_MARGIN, max_coord], 
            [max_coord, self.OUTER_MARGIN], 
            'k-', 
            linewidth=self.LINE_WIDTH_INNER
        )
    
    def get_ak_dk(self) -> Tuple[Optional[str], Optional[str]]:
        """Return Atmakaraka and Darakaraka planets"""
        return self.ak_planet, self.dk_planet
    
    def get_all_chara_karakas(self) -> List[Tuple[str, str]]:
        """
        Get all 7 Chara Karakas in order
        
        Returns:
            List of (karaka_name, planet_name) tuples
        """
        data = self._get_active_chart_data()
        planet_degrees: List[Tuple[str, float]] = []
        
        for planet_key, planet_data in data.items():
            if planet_key in self.EXCLUDED_KEYS:
                continue
            if planet_key.startswith('d') and '_chart' in planet_key:
                continue
            if not isinstance(planet_data, dict):
                continue
            if planet_key.lower() not in self.CHARA_KARAKA_PLANETS:
                continue
            
            degree = planet_data.get('degree', 0)
            planet_degrees.append((planet_key, float(degree)))
        
        planet_degrees.sort(key=lambda x: (-x[1], x[0]))
        
        karaka_names = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
        return [(karaka_names[i], planet_degrees[i][0]) for i in range(min(7, len(planet_degrees)))]
    
    def get_house_data(self):
        """
        House positions optimized for rashi number display
        Industry standard positioning
        """
        houses = {
            # House 1: Top triangle (Ascendant position)
            1: {
                'text_center': (5, 7.0),
                'rashi_pos': (5, 5.5),      # Ref (5,5), Up 0.5
                'font_size': 10
            },
            # House 2: Top-left small triangle
            2: {
                'text_center': (2.5, 8.5),  # Outer
                'rashi_pos': (3.0, 7.25),   # Ref (3,7), Up 0.25
                'font_size': 9
            },
            # House 3: Left-upper
            3: {
                'text_center': (1.7, 7.0),  # Outer
                'rashi_pos': (2.75, 7.0),   # Ref (3,7), Left 0.25
                'font_size': 9
            },
            # House 4: Left big triangle
            4: {
                'text_center': (3.0, 5.0),  # Symm H1
                'rashi_pos': (4.5, 5.0),    # Ref (5,5), Left 0.5
                'font_size': 10
            },
            # House 5: Left-lower
            5: {
                'text_center': (1.7, 3.0),  # Outer
                'rashi_pos': (2.75, 3.0),   # Ref (3,3), Left 0.25
                'font_size': 9
            },
            # House 6: Bottom-left small
            6: {
                'text_center': (3.0, 1.7),  # Outer
                'rashi_pos': (3.0, 2.75),   # Ref (3,3), Down 0.25
                'font_size': 9
            },
            # House 7: Bottom triangle
            7: {
                'text_center': (5, 3.0),    # Symm H1
                'rashi_pos': (5, 4.5),      # Ref (5,5), Down 0.5
                'font_size': 10
            },
            # House 8: Bottom-right small
            8: {
                'text_center': (7.0, 1.5),  # Outer
                'rashi_pos': (7.0, 2.75),   # Ref (7,3), Down 0.25
                'font_size': 9
            },
            # House 9: Right-lower
            9: {
                'text_center': (8.2, 3.0),  # Outer
                'rashi_pos': (7.25, 3.0),   # Ref (7,3), Right 0.25
                'font_size': 9
            },
            # House 10: Right big triangle
            10: {
                'text_center': (7.0, 5.0),  # Symm H1
                'rashi_pos': (5.5, 5.0),    # Ref (5,5), Right 0.5
                'font_size': 10
            },
            # House 11: Right-upper
            11: {
                'text_center': (8.2, 7.0),  # Outer
                'rashi_pos': (7.25, 7.0),   # Ref (7,7), Right 0.25
                'font_size': 9
            },
            # House 12: Top-right small
            12: {
                'text_center': (7.0, 8.08),  # Outer
                'rashi_pos': (7.0, 7.25),   # Ref (7,7), Up 0.25
                'font_size': 9
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
                bbox=None
            )
    
    def get_planets_by_house(self):
        """Group planets by house"""
        data = self.get_planets_for_display()
        
        planets_in_houses = {i: [] for i in range(1, 13)}
        
        for planet_key, planet_data in data.items():
            if not isinstance(planet_data, dict) or 'sign_num' not in planet_data:
                continue
            
            sign_num = planet_data.get('sign_num', 0)
            degree = planet_data.get('degree', 0)
            
            # Calculate house number from sign
            house_num = ((sign_num - self.ascendant_sign) % 12) + 1
            
            planet_name = self.PLANET_NAMES.get(planet_key, planet_key[:3])
            
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
                degree_val = planet['degree']
                
                # Format as Degree:Minute (e.g., 10°30') - Standard for Vedic Astrology
                d = int(degree_val)
                m = int((degree_val - d) * 60)
                text = f"{prefix}{name} {d}°{m:02d}'"
                
                # Smart truncation
                # If too long, try removing minutes first
                if len(text) > 15:
                    text_no_min = f"{prefix}{name} {d}°"
                    if len(text_no_min) <= 15:
                        text = text_no_min
                    else:
                        # If still too long, truncate name
                        text = text[:14] + '°'
                
                self.ax.text(
                    center_pos[0], y_pos, text,
                    ha='center', va='center',
                    fontsize=font_size,
                    color='#1a1a1a',      # Dark text
                    weight='bold',
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
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
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


def generate_single_varga(chart_data, chart_type, person_name='', output_dir='./generated_charts'):
    """Generate a single divisional chart on demand"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        renderer = NorthIndianChart(chart_data, chart_type, person_name)
        output_path = f"{output_dir}/{person_name}_{chart_type}_{timestamp}.png"
        renderer.render(output_path)
        return output_path
    except Exception as e:
        logger.error(f"Error generating {chart_type}: {e}")
        return None

def generate_all_charts(chart_data, person_name='', output_dir='./generated_charts'):
    """Generate primary divisional charts"""
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Primary charts to generate by default
    for chart_type in ['D1', 'D9', 'D10', 'D12']:
        results[chart_type] = generate_single_varga(chart_data, chart_type, person_name, output_dir)
    
    # Generate nakshatra table
    try:
        # Check if detailed_nakshatra_img exists in chart_data or handle separately
        pass # The app.py handles detailed table now
    except Exception as e:
        logger.error(f"Error generating nakshatra table: {e}")
    
    return results