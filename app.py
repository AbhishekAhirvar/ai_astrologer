# app.py
"""
Vedic Astrology AI - Tabs Layout + Detailed Nakshatra
"""

import gradio as gr
from backend.location import get_location_data
from backend.astrology import generate_chart_with_nakshatras
from backend.ai import get_astrology_prediction
from backend.chart_renderer import generate_all_charts
import time
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
import os

user_requests = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 10
CHARTS_DIR = "./generated_charts"

def check_rate_limit(identifier="default"):
    now = time.time()
    user_requests[identifier] = [t for t in user_requests[identifier] if now - t < 60]
    if len(user_requests[identifier]) >= MAX_REQUESTS_PER_MINUTE:
        return False
    user_requests[identifier].append(now)
    return True

def create_planetary_table_image(chart, output_path):
    """Create planetary positions table as PNG"""
    
    width = 900
    height = 650
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
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
        planet_data = chart.get(planet_key, {})
        nakshatra_data = planet_data.get('nakshatra', {})
        
        if idx % 2 == 0:
            draw.rectangle([30, y, width-30, y+40], fill='#f0f0f0')
        
        draw.rectangle([30, y, width-30, y+40], outline='#cccccc', width=1)
        
        draw.text((x_positions[0], y+12), planet_display, fill='black', font=text_font)
        draw.text((x_positions[1], y+12), planet_data.get('sign', 'N/A'), fill='black', font=text_font)
        draw.text((x_positions[2], y+12), f"{planet_data.get('degree', 0):.1f}°", fill='black', font=text_font)
        draw.text((x_positions[3], y+12), nakshatra_data.get('nakshatra', 'N/A'), fill='black', font=text_font)
        draw.text((x_positions[4], y+12), nakshatra_data.get('lord', 'N/A'), fill='black', font=text_font)
        
        y += 40
    
    img.save(output_path)
    return output_path

def create_detailed_nakshatra_table(chart, output_path):
    """Create detailed nakshatra analysis table like reference image"""
    
    width = 1100
    height = 750
    img = Image.new('RGB', (width, height), '#f5f5f5')
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    y = 25
    
    # Title
    draw.rectangle([0, 0, width, 70], fill='#888888')
    draw.text((width//2, 35), "NAKSHATRA-BASED ANALYSIS", fill='white', font=title_font, anchor="mm")
    
    y = 85
    
    # Table header
    headers = ['Planet', 'House', 'House(s)\nruled', 'Nakshatra', 'Nature', 'Caste']
    x_positions = [30, 220, 340, 480, 700, 880]
    col_widths = [190, 120, 140, 220, 180, 180]
    
    # Header background
    draw.rectangle([20, y, width-20, y+50], fill='#d0d0d0', outline='black', width=2)
    
    for i, header in enumerate(headers):
        # Draw vertical lines
        if i > 0:
            draw.line([(x_positions[i]-10, y), (x_positions[i]-10, y+50)], fill='black', width=1)
        
        header_lines = header.split('\n')
        if len(header_lines) == 2:
            draw.text((x_positions[i], y+15), header_lines[0], fill='black', font=header_font)
            draw.text((x_positions[i], y+32), header_lines[1], fill='black', font=header_font)
        else:
            draw.text((x_positions[i], y+25), header, fill='black', font=header_font, anchor="lm")
    
    y += 50
    
    # Planets data with house calculations
    planets_info = [
        ('Ascendant', 'ascendant', 1, '-'),
        ('Jupiter\n(Brahmin - Ministerial)', 'jupiter', None, '9,12'),
        ('Saturn\n(Shudras - Service)', 'saturn', None, '10,11'),
        ('Moon\n(Merchant - Royal)', 'moon', None, '4'),
        ('Sun\n(Kshatriya - Royal)', 'sun', None, '5'),
        ('Mercury\n(Merchant - Prince)', 'mercury', None, '3,6'),
        ('Rahu', 'rahu', None, '11'),
        ('Venus\n(Brahmin - Ministerial)', 'venus', None, '2,7'),
        ('Mars\n(Kshatriya - Army Chief)', 'mars', None, '1,8'),
        ('Ketu', 'ketu', None, '8'),
    ]
    
    for idx, (planet_display, planet_key, house_num, houses_ruled) in enumerate(planets_info):
        planet_data = chart.get(planet_key, {})
        nakshatra_data = planet_data.get('nakshatra', {})
        
        # Calculate house if not provided
        if house_num is None:
            sign_num = planet_data.get('sign_num', 0)
            ascendant_sign = chart.get('ascendant', {}).get('sign_num', 0)
            house_num = ((sign_num - ascendant_sign) % 12) + 1
        
        # Row background
        if idx % 2 == 0:
            draw.rectangle([20, y, width-20, y+50], fill='white', outline='#cccccc', width=1)
        else:
            draw.rectangle([20, y, width-20, y+50], fill='#f9f9f9', outline='#cccccc', width=1)
        
        # Vertical lines
        for i in range(1, len(x_positions)):
            draw.line([(x_positions[i]-10, y), (x_positions[i]-10, y+50)], fill='#cccccc', width=1)
        
        # Data
        planet_lines = planet_display.split('\n')
        if len(planet_lines) == 2:
            draw.text((x_positions[0], y+12), planet_lines[0], fill='black', font=text_font)
            draw.text((x_positions[0], y+30), planet_lines[1], fill='black', font=small_font)
        else:
            draw.text((x_positions[0], y+25), planet_display, fill='black', font=text_font, anchor="lm")
        
        draw.text((x_positions[1], y+25), str(house_num), fill='black', font=text_font, anchor="lm")
        draw.text((x_positions[2], y+25), houses_ruled, fill='black', font=text_font, anchor="lm")
        
        # Nakshatra with pada
        nak_name = nakshatra_data.get('nakshatra', 'N/A')
        pada = nakshatra_data.get('pada', 'N/A')
        sign = planet_data.get('sign', 'N/A')
        nak_text = f"{nak_name}\n({pada} - {sign})"
        nak_lines = nak_text.split('\n')
        draw.text((x_positions[3], y+15), nak_lines[0], fill='black', font=text_font)
        draw.text((x_positions[3], y+32), nak_lines[1], fill='black', font=small_font)
        
        # Nature
        nature = nakshatra_data.get('element', 'N/A')
        draw.text((x_positions[4], y+25), nature, fill='black', font=text_font, anchor="lm")
        
        # Caste
        caste_map = {
            'jupiter': 'Brahmin',
            'venus': 'Brahmin',
            'moon': 'Merchant',
            'mercury': 'Merchant',
            'sun': 'Kshatriya',
            'mars': 'Kshatriya',
            'saturn': 'Shudra',
            'rahu': 'Outcaste',
            'ketu': 'Outcaste',
            'ascendant': 'Merchant'
        }
        caste = caste_map.get(planet_key, 'N/A')
        draw.text((x_positions[5], y+25), caste, fill='black', font=text_font, anchor="lm")
        
        y += 50
    
    img.save(output_path)
    return output_path

def generate_report(name, gender, dob_date, dob_time, place_name):
    """Generate birth chart with all tables"""
    if not all([name, gender, dob_date, dob_time, place_name]):
        return "❌ Please fill all fields!", None, None, None, None, None, None, None

    loc_data = get_location_data(place_name)
    if not loc_data:
        return "❌ Location not found.", None, None, None, None, None, None, None
    
    lat, lon, address = loc_data

    try:
        year, month, day = map(int, dob_date.split("-"))
        hour, minute = map(int, dob_time.split(":"))
    except ValueError:
        return "❌ Invalid Date/Time.", None, None, None, None, None, None, None

    chart = generate_chart_with_nakshatras(name, year, month, day, hour, minute, place_name, lat, lon)
    
    if '_metadata' in chart:
        chart['_metadata']['gender'] = gender
    
    if "error" in chart:
        return f"❌ Error: {chart['error']}", None, None, None, None, None, None, None

    try:
        chart_images = generate_all_charts(chart, person_name=name, output_dir=CHARTS_DIR)
    except Exception as e:
        return f"⚠️ Error: {str(e)}", None, None, None, None, None, None, None

    metadata = chart.get('_metadata', {})
    moon_naks = chart['moon'].get('nakshatra', {})
    
    summary_text = f"""
## 🌟 Birth Chart: {name}

**👤 Gender:** {gender}  
**📍 Location:** {address}  
**📅 Date/Time:** {dob_date} at {dob_time}  
**🌌 System:** {metadata.get('zodiac_system', 'Sidereal (Lahiri)')}

---

### 🌙 PRIMARY MOON NAKSHATRA

**Nakshatra:** {moon_naks.get('nakshatra', 'N/A')}  
**Lord:** {moon_naks.get('lord', 'N/A')}  
**Pada:** {moon_naks.get('pada', 'N/A')}/4  
**Symbol:** {moon_naks.get('symbol', 'N/A')}  
**Element:** {moon_naks.get('element', 'N/A')}

✅ **Charts generated! Check tabs below.**
"""
    
    # Create tables
    timestamp = int(time.time())
    table_path = os.path.join(CHARTS_DIR, f"{name}_planetary_table_{timestamp}.png")
    nak_table_path = os.path.join(CHARTS_DIR, f"{name}_nakshatra_detailed_{timestamp}.png")
    
    create_planetary_table_image(chart, table_path)
    create_detailed_nakshatra_table(chart, nak_table_path)
    
    d1_img = chart_images.get('D1')
    d9_img = chart_images.get('D9')
    d10_img = chart_images.get('D10')
    d12_img = chart_images.get('D12')
    
    return summary_text, table_path, nak_table_path, d1_img, d9_img, d10_img, d12_img, chart


# UI
with gr.Blocks(title="Vedic Astrology AI") as demo:
    
    chart_state = gr.State(None)
    
    gr.HTML("""
    <div style='text-align: center; padding: 20px;'>
        <h1>🌟 Vedic Astrology AI</h1>
        <p>Birth Charts • Nakshatras • Divisional Charts • AI Predictions</p>
    </div>
    """)
    
    with gr.Tabs():
        
        # TAB 1: Chart Generator
        with gr.Tab("📊 Birth Chart Generator"):
            gr.Markdown("### Enter Birth Details")
            
            with gr.Row():
                name = gr.Textbox(label="Name", placeholder="John Doe")
                gender = gr.Radio(["Male", "Female", "Other"], label="Gender", value="Male")
            
            with gr.Row():
                dob_date = gr.Textbox(label="Birth Date", placeholder="YYYY-MM-DD", value="1990-01-15")
                dob_time = gr.Textbox(label="Birth Time", placeholder="HH:MM", value="12:30")
            
            place_name = gr.Textbox(label="Birth Place", placeholder="New Delhi, India", value="New Delhi")
            
            generate_btn = gr.Button("🔮 Generate Chart", variant="primary", size="lg")
            
            chart_summary = gr.Markdown()
            
            # Charts in TABS (not all at once)
            with gr.Tabs():
                with gr.Tab("📋 Planetary Positions"):
                    planetary_table_img = gr.Image(label="Planetary Positions Table", height=450)
                
                with gr.Tab("🌙 Nakshatra Analysis"):
                    nakshatra_detailed_img = gr.Image(label="Detailed Nakshatra Analysis", height=500)
                
                with gr.Tab("🎯 D1 - Rasi Chart"):
                    d1_chart = gr.Image(label="D1 Birth Chart", height=500)
                
                with gr.Tab("💍 D9 - Navamsa"):
                    d9_chart = gr.Image(label="D9 Marriage Chart", height=500)
                
                with gr.Tab("💼 D10 - Dasamsa"):
                    d10_chart = gr.Image(label="D10 Career Chart", height=500)
                
                with gr.Tab("👨‍👩‍👧 D12 - Dwadasamsa"):
                    d12_chart = gr.Image(label="D12 Family Chart", height=500)
        
        # TAB 2: AI Chat
        with gr.Tab("🤖 Ask AI Astrologer"):
            gr.Markdown("""
            ### Chat with AI Astrologer
            Generate your birth chart first, then ask any questions!
            
            **The AI knows:**
            - Your planetary positions & nakshatras
            - All divisional charts (D9, D10, D12)
            - Vedic astrology principles
            """)

            def chat_response(message, history, chart_data):
                """Handle chat interactions"""
                if not chart_data:
                    return "⚠️ Please generate a birth chart first in the 'Birth Chart Generator' tab!"
                
                if not check_rate_limit():
                    return "⚠️ Rate limit exceeded. Please wait a minute."
                
                if len(message) > 500:
                    return "⚠️ Question too long. Keep it under 500 characters."
                
                response = get_astrology_prediction(chart_data, message)
                return response

            gr.ChatInterface(
                fn=chat_response,
                additional_inputs=[chart_state],
                examples=[
                    ["What does my Sun sign mean?"],
                    ["Tell me about my Moon placement"],
                    ["What career suits my chart?"],
                    ["Analyze my relationships based on Venus"]
                ]
            )
    
    # Wire generate button
    generate_btn.click(
        generate_report,
        [name, gender, dob_date, dob_time, place_name],
        [chart_summary, planetary_table_img, nakshatra_detailed_img, d1_chart, d9_chart, d10_chart, d12_chart, chart_state]
    )


if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860)
