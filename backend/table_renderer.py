from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Union, Any
from backend.schemas import ChartResponse, PlanetPosition

def get_font(font_type="bold", size=14):
    """Helper to load fonts safely"""
    try:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if font_type == "bold" else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def create_planetary_table_image(chart: Union[Dict, Any], output_path: str) -> str:
    """
    Create planetary positions table as PNG.
    Accepts specific chart dict or Pydantic model.
    """
    
    width = 900
    height = 650
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    title_font = get_font("bold", 24)
    header_font = get_font("bold", 16)
    text_font = get_font("bold", 14)
    
    y = 30
    
    # Title
    draw.text((width//2, y), "PLANETARY POSITIONS", fill='black', font=title_font, anchor="mt")
    y += 60
    
    # Header
    draw.rectangle([30, y, width-30, y+40], outline='black', fill='#4A90E2', width=2)
    headers = ['Planet', 'Sign', 'Degree', 'Nakshatra', 'Lord']
    x_positions = [50, 200, 350, 480, 700]
    
    for i, header in enumerate(headers):
        draw.text((x_positions[i], y+12), header, fill='white', font=header_font)
    
    y += 40
    
    planets = [
        ('Sun', 'sun'),
        ('Moon', 'moon'),
        ('Ascendant', 'ascendant'),
        ('Mercury', 'mercury'),
        ('Venus', 'venus'),
        ('Mars', 'mars'),
        ('Jupiter', 'jupiter'),
        ('Saturn', 'saturn'),
        ('Rahu', 'rahu'),
        ('Ketu', 'ketu'),
    ]
    
    for idx, (planet_display, planet_key) in enumerate(planets):
        # Handle both Dict and Pydantic Model access
        if isinstance(chart, dict):
            # Dict access
            planet_data = chart.get(planet_key, {})
            # If chart.get returned a model (unlikely if chart is dict, but possible in hybrid)
            if hasattr(planet_data, 'dict'): planet_data = planet_data.dict()
        else:
            # Model access (ChartResponse has .planets dict)
            # Or if chart is the planets dict itself
            if hasattr(chart, 'planets'):
                planet_data = getattr(chart.planets, 'get', lambda k,d: d)(planet_key, {})
            else:
                planet_data = chart.get(planet_key, {})
            
            if hasattr(planet_data, 'dict'): planet_data = planet_data.dict()

        nakshatra_data = planet_data.get('nakshatra', {})
        if hasattr(nakshatra_data, 'dict'): nakshatra_data = nakshatra_data.dict()
        
        if idx % 2 == 0:
            draw.rectangle([30, y, width-30, y+40], fill='#f0f0f0')
        
        draw.rectangle([30, y, width-30, y+40], outline='#cccccc', width=1)
        
        draw.text((x_positions[0], y+12), planet_display, fill='black', font=text_font)
        draw.text((x_positions[1], y+12), str(planet_data.get('sign', 'N/A')), fill='black', font=text_font)
        
        deg = planet_data.get('degree', 0)
        minutes = int((deg % 1) * 60)
        seconds = int(((deg % 1) * 60 % 1) * 60)
        deg_str = f"{int(deg):02d}°{minutes:02d}'{seconds:02d}\""
        
        draw.text((x_positions[2], y+12), deg_str, fill='black', font=text_font)
        draw.text((x_positions[3], y+12), str(nakshatra_data.get('nakshatra', 'N/A')), fill='black', font=text_font)
        draw.text((x_positions[4], y+12), str(nakshatra_data.get('lord', 'N/A')), fill='black', font=text_font)
        
        y += 40
    
    img.save(output_path)
    return output_path

def create_detailed_nakshatra_table(chart: Union[Dict, Any], output_path: str) -> str:
    """Create detailed nakshatra analysis table like reference image"""
    
    width = 1200
    height = 800
    img = Image.new('RGB', (width, height), 'white') # Light theme
    draw = ImageDraw.Draw(img)
    
    title_font = get_font("bold", 24)
    header_font = get_font("bold", 14)
    text_font = get_font("bold", 13)
    
    y = 0
    
    # Title Line
    draw.rectangle([0, 0, width, 50], fill='#4A90E2')
    draw.text((20, 25), "Nakshatra-based Analysis", fill='#ffffff', font=title_font, anchor="lm")
    
    y = 60
    
    # Table header
    headers = ['Planet', 'Karaka', 'Degrees', 'Rasi', 'Navamsa', 'Nakshatra (Pada, Lord)', 'Relationship', 'House', 'Lord']
    x_positions = [20, 140, 230, 340, 460, 580, 820, 960, 1060]
    
    # Header background
    draw.rectangle([0, y, width, y+40], fill='#4A90E2')
    
    # Make header text white and bold
    for i, header in enumerate(headers):
        draw.text((x_positions[i], y+20), header, fill='white', font=header_font, anchor="lm")
    
    y += 50
    
    planets_order = [
        ('Ascendant', 'ascendant'),
        ('Sun', 'sun'),
        ('Moon', 'moon'),
        ('Mars', 'mars'),
        ('Mercury', 'mercury'),
        ('Jupiter', 'jupiter'),
        ('Venus', 'venus'),
        ('Saturn', 'saturn'),
        ('Rahu', 'rahu'),
        ('Ketu', 'ketu'),
    ]
    
    for idx, (display_name, key) in enumerate(planets_order):
        # Access logic compatible with dict and Pydantic
        if isinstance(chart, dict):
            planet_data = chart.get(key, {})
            if hasattr(planet_data, 'dict'): planet_data = planet_data.dict()
            
            # Navamsa access
            d9_chart = chart.get('d9_chart', {})
            if hasattr(d9_chart, 'get'):
                d9_data = d9_chart.get(key, {})
            else:
                d9_data = {}
            if hasattr(d9_data, 'dict'): d9_data = d9_data.dict()

        else:
            # Model access
            if hasattr(chart, 'planets'):
                planet_data = getattr(chart.planets, 'get', lambda k,d: d)(key, {})
            else:
                planet_data = chart.get(key, {})
            if hasattr(planet_data, 'dict'): planet_data = planet_data.dict()
            
            # Navamsa attached to chart response
            if hasattr(chart, 'vargas'):
                d9_chart = chart.vargas.get('d9_chart', {})
                d9_data = d9_chart.get(key, {}) if d9_chart else {}
            else:
                d9_data = {}
            if hasattr(d9_data, 'dict'): d9_data = d9_data.dict()
            
        if not planet_data: continue

        row_height = 50
        
        if idx % 2 == 0:
            draw.rectangle([10, y, width-10, y+row_height], fill='#f0f0f0')
            
        draw.rectangle([10, y, width-10, y+row_height], outline='#cccccc', width=1)
        
        # Name
        draw.text((x_positions[0], y+25), display_name, fill='black', font=text_font, anchor="lm")
        
        # Karaka
        draw.text((x_positions[1], y+25), str(planet_data.get('karaka', '-')), fill='black', font=text_font, anchor="lm")
        
        # Degrees
        deg = planet_data.get('degree', 0)
        minutes = int((deg % 1) * 60)
        seconds = int(((deg % 1) * 60 % 1) * 60)
        deg_str = f"{int(deg):02d}°{minutes:02d}'{seconds:02d}\""
        draw.text((x_positions[2], y+25), deg_str, fill='black', font=text_font, anchor="lm")
        
        # Rasi
        draw.text((x_positions[3], y+25), str(planet_data.get('sign', 'N/A')), fill='black', font=text_font, anchor="lm")
        
        # Navamsa (D9)
        draw.text((x_positions[4], y+25), str(d9_data.get('sign', 'N/A')), fill='black', font=text_font, anchor="lm")
        
        # Nakshatra (Pada, Lord)
        nak_info = planet_data.get('nakshatra', {})
        if hasattr(nak_info, 'dict'): nak_info = nak_info.dict()
        
        nak_text = f"{nak_info.get('nakshatra', 'N/A')} ({nak_info.get('pada', 'N/A')}, {str(nak_info.get('lord', 'N/A'))[:2]})"
        draw.text((x_positions[5], y+25), nak_text, fill='black', font=text_font, anchor="lm")
        
        # Relationship
        draw.text((x_positions[6], y+25), str(planet_data.get('relationship', 'Neutral')), fill='black', font=text_font, anchor="lm")
        
        # House
        draw.text((x_positions[7], y+25), str(planet_data.get('house', '-')), fill='black', font=text_font, anchor="lm")
        
        # Lord
        draw.text((x_positions[8], y+25), str(planet_data.get('rules_houses', '-')), fill='black', font=text_font, anchor="lm")
        
        y += row_height
    
    img.save(output_path)
    return output_path
