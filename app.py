# app.py
"""
Vedic Astrology AI - Tabs Layout + Detailed Nakshatra
"""

import gradio as gr
from backend.location import get_location_data
from backend.astrology import generate_vedic_chart
from backend.ai import get_astrology_prediction
from backend.chart_renderer import generate_all_charts, generate_single_varga
from backend.logger import logger
import time
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

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

def cleanup_old_charts(directory, max_age_seconds=3600):
    """Delete files in directory older than max_age_seconds or just clear it"""
    if not os.path.exists(directory):
        return
    
    now = time.time()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                # For now, let's just clear everything to be sure "purana delete ho jaye"
                # If you want to keep files for a while, use: if now - os.path.getmtime(file_path) > max_age_seconds:
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")

def create_planetary_table_image(chart, output_path):
    """Create planetary positions table as PNG"""
    
    width = 900
    height = 650
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
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
        deg = planet_data.get('degree', 0)
        minutes = int((deg % 1) * 60)
        seconds = int(((deg % 1) * 60 % 1) * 60)
        deg_str = f"{int(deg):02d}°{minutes:02d}'" # Shortened DMS for this table as space is tight, or just use same format?
        # User wants consistency.
        # Planetary Table Space: column 3 is at x=350. Next is 480. 130px width.
        # "28°59'59"" is approx 10 chars. Sans font 14px. Should fit.
        deg_str = f"{int(deg):02d}°{minutes:02d}'{seconds:02d}\""
        
        draw.text((x_positions[0], y+12), planet_display, fill='black', font=text_font)
        draw.text((x_positions[1], y+12), planet_data.get('sign', 'N/A'), fill='black', font=text_font)
        draw.text((x_positions[2], y+12), deg_str, fill='black', font=text_font)
        draw.text((x_positions[3], y+12), nakshatra_data.get('nakshatra', 'N/A'), fill='black', font=text_font)
        draw.text((x_positions[4], y+12), nakshatra_data.get('lord', 'N/A'), fill='black', font=text_font)
        
        y += 40
    
    img.save(output_path)
    return output_path

def create_detailed_nakshatra_table(chart, output_path):
    """Create detailed nakshatra analysis table like reference image"""
    
    width = 1200
    height = 800
    img = Image.new('RGB', (width, height), 'white') # Light theme
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
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
        planet_data = chart.get(key, {})
        if not planet_data: continue
        
        # Consistent Styling with Planetary Table
        # Row background (alternating is fine, but lets match the "Card" look if requested, 
        # but user said "consistent". The Planetary table has a specific outline style.
        # Let's try to mimic that outline style here too, but this table is wider.
        
        # Planetary table logic:
        # if idx % 2 == 0: draw.rectangle(..., fill='#f0f0f0')
        # draw.rectangle(..., outline='#cccccc', width=1)
        
        row_height = 50
        
        if idx % 2 == 0:
            draw.rectangle([10, y, width-10, y+row_height], fill='#f0f0f0')
            
        draw.rectangle([10, y, width-10, y+row_height], outline='#cccccc', width=1)
        
        # Name
        draw.text((x_positions[0], y+25), display_name, fill='black', font=text_font, anchor="lm")
        
        # Karaka
        draw.text((x_positions[1], y+25), planet_data.get('karaka', '-'), fill='black', font=text_font, anchor="lm")
        
        # Degrees
        deg = planet_data.get('degree', 0)
        minutes = int((deg % 1) * 60)
        seconds = int(((deg % 1) * 60 % 1) * 60)
        deg_str = f"{int(deg):02d}°{minutes:02d}'{seconds:02d}\""
        draw.text((x_positions[2], y+25), deg_str, fill='black', font=text_font, anchor="lm")
        
        # Rasi
        draw.text((x_positions[3], y+25), planet_data.get('sign', 'N/A'), fill='black', font=text_font, anchor="lm")
        
        # Navamsa (D9)
        d9_data = chart.get('d9_chart', {}).get(key, {})
        draw.text((x_positions[4], y+25), d9_data.get('sign', 'N/A'), fill='black', font=text_font, anchor="lm")
        
        # Nakshatra (Pada, Lord)
        nak_info = planet_data.get('nakshatra', {})
        nak_text = f"{nak_info.get('nakshatra', 'N/A')} ({nak_info.get('pada', 'N/A')}, {nak_info.get('lord', 'N/A')[:2]})"
        draw.text((x_positions[5], y+25), nak_text, fill='black', font=text_font, anchor="lm")
        
        # Relationship
        draw.text((x_positions[6], y+25), planet_data.get('relationship', 'Neutral'), fill='black', font=text_font, anchor="lm")
        
        # House
        draw.text((x_positions[7], y+25), str(planet_data.get('house', '-')), fill='black', font=text_font, anchor="lm")
        
        # Lord
        draw.text((x_positions[8], y+25), planet_data.get('rules_houses', '-'), fill='black', font=text_font, anchor="lm")
        
        y += row_height
    
    img.save(output_path)
    return output_path

def generate_report(name, gender, dob_date, dob_time, place_name):
    """Generate birth chart with all tables"""
    # Validation
    if not all([name, dob_date, dob_time, place_name]):
        logger.warning(f"Registration failed: Missing fields for {name or 'Unknown'}")
        return "⚠️ All fields are required!", None, None, None, None, None, None, None

    logger.info(f"Generating report for: {name} ({dob_date} {dob_time}) at {place_name}")

    # Step 0: Cleanup old charts
    cleanup_old_charts(CHARTS_DIR)

    # Step 1: Validate Date Format & Logic
    try:
        # Flexible Date Parsing
        # Try different formats
        dob_dt = None
        formats_to_try = [
            "%Y-%m-%d", # 2023-05-20
            "%d-%m-%Y", # 20-05-2023
            "%d/%m/%Y", # 20/05/2023
            "%Y/%m/%d", # 2023/05/20
            "%d%m%Y",   # 20052023
            "%Y%m%d"    # 20230520
        ]
        
        # Sanitize input: remove extra spaces
        clean_date = dob_date.strip()
        
        # If user just typed DDMMYYYY without separators
        if len(clean_date) == 8 and clean_date.isdigit():
             # Ambiguity check: 01022023 -> 1st Feb or 2nd Jan?
             # Standard assumptions: if first part > 12 likely DD.
             # We will try DDMMYYYY first as it's common in India/UK.
             formats_to_try = ["%d%m%Y", "%Y%m%d"]
        
        for fmt in formats_to_try:
            try:
                dob_dt = datetime.strptime(clean_date, fmt)
                break
            except ValueError:
                continue
                
        if not dob_dt:
             raise ValueError("No valid format found")
             
        year, month, day = dob_dt.year, dob_dt.month, dob_dt.day
        
        # Normalize date string for display/logging
        dob_date = dob_dt.strftime("%Y-%m-%d")
        
        if not (1800 <= year <= 2100):
            return f"❌ Year {year} is out of range (1800-2100).", None, None, None, None, None, None, None
            
    except ValueError:
        return "❌ Invalid Date format. Use YYYY-MM-DD, DD-MM-YYYY or just DDMMYYYY.", None, None, None, None, None, None, None

    # Step 2: Validate Time Format
    try:
        # Check format HH:MM
        time_parts = dob_time.split(":")
        if len(time_parts) != 2:
            raise ValueError
            
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return "❌ Invalid Time. Hours must be 0-23 and minutes 0-59.", None, None, None, None, None, None, None
            
    except ValueError:
        return "❌ Invalid Time format. Use HH:MM (e.g., 14:30).", None, None, None, None, None, None, None

    # Step 3: Fetch Location Data
    loc_data = get_location_data(place_name)
    if not loc_data:
        return f"❌ Location '{place_name}' not found. Please check the name.", None, None, None, None, None, None, None
    
    lat, lon, address = loc_data
    logger.info(f"Location resolved: {address} ({lat}, {lon})")

    chart = generate_vedic_chart(name, year, month, day, hour, minute, place_name, lat, lon)
    
    if '_metadata' in chart:
        chart['_metadata']['gender'] = gender
    
    if "error" in chart:
        logger.error(f"Vedic chart generation error: {chart['error']}")
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
    
    return summary_text, table_path, nak_table_path, d1_img, chart

def update_varga_display(chart_data, varga_type):
    """Update varga chart image based on dropdown selection"""
    if not chart_data:
        return None
    
    # Map label to chart key
    mapping = {
        "D1 Rasi": "D1",
        "Moon Chart": "Moon",
        "Sun Chart": "Sun",
        "Arudha Lagna": "Arudha"
    }
    
    chart_code = mapping.get(varga_type)
    if not chart_code:
        # Extract D number from string like "D9 Navamsa" -> "D9"
        chart_code = varga_type.split(' ')[0]
    
    name = chart_data.get('_metadata', {}).get('name', 'User')
    img_path = generate_single_varga(chart_data, chart_code, person_name=name, output_dir=CHARTS_DIR)
    return img_path


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
                dob_date = gr.Textbox(label="Birth Date", placeholder="YYYY-MM-DD", value=datetime.now().strftime("%Y-%m-%d"))
                dob_time = gr.Textbox(label="Birth Time", placeholder="HH:MM", value=datetime.now().strftime("%H:%M"))
            
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
                
                with gr.Tab("💠 Divisional Charts (Vargas)"):
                    with gr.Row():
                        varga_select = gr.Dropdown(
                            label="Select Varga Chart",
                            choices=[
                                "D1 Rasi", "Moon Chart", "Sun Chart", "Arudha Lagna",
                                "D2 Hora", "D3 Drekkana", "D4 Chaturthamsa", 
                                "D5 Panchamsa", "D6 Shashtamsa", "D7 Saptamsa", "D8 Ashtamsa",
                                "D9 Navamsa", "D10 Dasamsa", "D11 Rudramsa", "D12 Dwadasamsa",
                                "D16 Shodasamsa", "D20 Vimsamsa", "D24 Siddhamsa", 
                                "D27 Nakshatramsa", "D30 Trimsamsa", "D40 Khavedamsa", 
                                "D45 Akshavedamsa", "D60 Shashtyamsa"
                            ],
                            value="D9 Navamsa"
                        )
                    varga_chart_img = gr.Image(label="Varga Chart", height=500)
        
        # TAB 2: Vedic AI Chat
        with gr.Tab("🕉️ Vedic AI Chat"):
            with gr.Row():
                # SIDEBAR (Left)
                with gr.Column(scale=1):
                    gr.Markdown("### ❓ Vedic Quick Questions")
                    vedic_examples = [
                        "💡 Will higher education help me?",
                        "🎉 Will party lifestyle help me?",
                        "🧭 Friends or family: who helps me?",
                        "💍 Will marriage bring me happiness?",
                        "🧘‍ Will monk life benefit me?",
                        "✈️ Can travel improve my life?",
                        "📈 Will I succeed in stock trading?",
                        "⭐ Will I become famous?",
                        "💰 Will I become a millionaire?",
                        "👤 Describe my future spouse?",
                        "👨‍👧 Relationship with my father?",
                        "🎟️ Can I win the lottery?",
                        "🔍 Special yogas in my chart?",
                        "💼 Best career path for me?",
                        "🌏 Will I get foreign education?"
                    ]
                    
                    vedic_q_btns = []
                    for ex in vedic_examples:
                        vedic_q_btns.append(gr.Button(ex, variant="ghost", size="sm"))

                # MAIN CHAT (Right)
                with gr.Column(scale=3):
                    gr.Markdown("### 🕉️ Expert Vedic Astrologer")
                    v_chatbot = gr.Chatbot(label="Vedic Astrology Chat", height=500)
                    
                    with gr.Column() as v_suggestion_row:
                        v_s_btn1 = gr.Button("", visible=False, size="sm")
                        v_s_btn2 = gr.Button("", visible=False, size="sm")
                        v_s_btn3 = gr.Button("", visible=False, size="sm")
                    
                    v_msg = gr.Textbox(label="Ask Vedic Astrology", placeholder="Ask any question about your life...", scale=7)

        # TAB 3: KP AI Chat
        with gr.Tab("🧭 KP AI Chat"):
            with gr.Row():
                # SIDEBAR (Left)
                with gr.Column(scale=1):
                    gr.Markdown("### 🔭 KP Quick Questions")
                    kp_examples = [
                        "🎯 Who is the sub-lord of my 10th house?",
                        "💼 Which planets are significators for my career?",
                        "🌟 What are my ruling planets right now?",
                        "💍 KP analysis: When will I get married?",
                        "📈 Which house cusp signifies business success?",
                        "🌏 Will I travel abroad according to KP?",
                        "🏦 Financial significators in my chart?",
                        "🛡️ My strongest house significator?",
                        "🔍 Sub-lord of my 7th house (Marriage)?",
                        "📉 Career obstacles in KP chart?"
                    ]
                    
                    kp_q_btns = []
                    for ex in kp_examples:
                        kp_q_btns.append(gr.Button(ex, variant="ghost", size="sm"))

                # MAIN CHAT (Right)
                with gr.Column(scale=3):
                    gr.Markdown("### 🔭 Expert KP Astrologer")
                    kp_chatbot = gr.Chatbot(label="KP Astrology Chat", height=500)
                    
                    with gr.Column() as kp_suggestion_row:
                        kp_s_btn1 = gr.Button("", visible=False, size="sm")
                        kp_s_btn2 = gr.Button("", visible=False, size="sm")
                        kp_s_btn3 = gr.Button("", visible=False, size="sm")
                    
                    kp_msg = gr.Textbox(label="Ask KP Astrology", placeholder="Ask using Krishnamurti Paddhati rules...", scale=7)

            def parse_ai_response(response):
                """Extract text and suggestions from AI response using || separator"""
                if "[SUGGESTIONS]" in response:
                    parts = response.split("[SUGGESTIONS]")
                    text = parts[0].strip()
                    # Split by || for robust separation
                    sug_raw = parts[1].split("||")
                    suggestions = [s.strip(" -.?*\"") + "?" for s in sug_raw if s.strip()]
                    return text, suggestions[:3]
                return response, []

            def handle_chat_input(user_input, history, chart_data, is_kp=False):
                """Unified chat entry point for Gradio 6.0"""
                if not chart_data:
                    error_msg = "⚠️ Please generate a birth chart first in the first tab!"
                    history.append({"role": "user", "content": user_input})
                    history.append({"role": "assistant", "content": error_msg})
                    return history, "", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
                
                if not check_rate_limit():
                    logger.warning(f"Rate limit exceeded for {user_input[:20]}...")
                    history.append({"role": "user", "content": user_input})
                    history.append({"role": "assistant", "content": "⚠️ Rate limit exceeded. Please wait a minute."})
                    return history, "", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
                
                # Append user message
                history.append({"role": "user", "content": user_input})
                
                # Get AI response
                response = get_astrology_prediction(chart_data, user_input, is_kp_mode=is_kp)
                text, suggestions = parse_ai_response(response)
                
                # Append assistant response
                history.append({"role": "assistant", "content": text})
                
                # Dynamic updates
                s1 = gr.update(value=suggestions[0], visible=True) if len(suggestions) > 0 else gr.update(visible=False)
                s2 = gr.update(value=suggestions[1], visible=True) if len(suggestions) > 1 else gr.update(visible=False)
                s3 = gr.update(value=suggestions[2], visible=True) if len(suggestions) > 2 else gr.update(visible=False)
                
                return history, "", s1, s2, s3

            # VEDIC EVENTS
            v_msg.submit(
                lambda u, h, c: handle_chat_input(u, h, c, False),
                [v_msg, v_chatbot, chart_state], 
                [v_chatbot, v_msg, v_s_btn1, v_s_btn2, v_s_btn3]
            )
            for qb in vedic_q_btns:
                qb.click(
                    lambda u, h, c: handle_chat_input(u, h, c, False),
                    [qb, v_chatbot, chart_state],
                    [v_chatbot, v_msg, v_s_btn1, v_s_btn2, v_s_btn3]
                )
            for sb in [v_s_btn1, v_s_btn2, v_s_btn3]:
                sb.click(
                    lambda u, h, c: handle_chat_input(u, h, c, False),
                    [sb, v_chatbot, chart_state],
                    [v_chatbot, v_msg, v_s_btn1, v_s_btn2, v_s_btn3]
                )

            # KP EVENTS
            kp_msg.submit(
                lambda u, h, c: handle_chat_input(u, h, c, True),
                [kp_msg, kp_chatbot, chart_state], 
                [kp_chatbot, kp_msg, kp_s_btn1, kp_s_btn2, kp_s_btn3]
            )
            for qb in kp_q_btns:
                qb.click(
                    lambda u, h, c: handle_chat_input(u, h, c, True),
                    [qb, kp_chatbot, chart_state],
                    [kp_chatbot, kp_msg, kp_s_btn1, kp_s_btn2, kp_s_btn3]
                )
            for sb in [kp_s_btn1, kp_s_btn2, kp_s_btn3]:
                sb.click(
                    lambda u, h, c: handle_chat_input(u, h, c, True),
                    [sb, kp_chatbot, chart_state],
                    [kp_chatbot, kp_msg, kp_s_btn1, kp_s_btn2, kp_s_btn3]
                )
    
    # Wire generate button
    generate_btn.click(
        generate_report,
        [name, gender, dob_date, dob_time, place_name],
        [chart_summary, planetary_table_img, nakshatra_detailed_img, d1_chart, chart_state]
    ).then(
        update_varga_display,
        [chart_state, varga_select],
        [varga_chart_img]
    )
    
    # Update varga on dropdown change
    varga_select.change(
        update_varga_display,
        [chart_state, varga_select],
        [varga_chart_img]
    )


if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860)
