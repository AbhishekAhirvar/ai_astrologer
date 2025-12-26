# app.py
"""
Vedic Astrology AI - Tabs Layout + Detailed Nakshatra
"""

import gradio as gr
from backend.location import get_location_data
from backend.astrology import generate_vedic_chart
from backend.ai import get_astrology_prediction
from backend.chart_renderer import generate_all_charts
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
    
    width = 1200
    height = 800
    img = Image.new('RGB', (width, height), '#1e1e1e') # Dark theme
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    y = 0
    
    # Title Line
    draw.rectangle([0, 0, width, 50], fill='#2d2d2d')
    draw.text((20, 25), "Nakshatra-based Analysis", fill='#ffffff', font=title_font, anchor="lm")
    
    y = 60
    
    # Table header
    headers = ['D1 R v', 'Karaka', 'Degrees', 'Rasi', 'Navamsa', 'Nakshatra (Pada, Lord)', 'Relationship', 'House', 'Lord']
    x_positions = [20, 140, 230, 340, 460, 580, 820, 960, 1060]
    
    # Header background
    draw.rectangle([0, y, width, y+40], fill='#2d2d2d')
    
    for i, header in enumerate(headers):
        draw.text((x_positions[i], y+20), header, fill='#b0b0b0', font=header_font, anchor="lm")
    
    y += 50
    
    planets_order = [
        ('Ascendant', 'ascendant', '#a594f9'),
        ('Sun', 'sun', '#ff7e67'),
        ('Moon', 'moon', '#6ebfb5'),
        ('Mars', 'mars', '#ff5c5c'),
        ('Mercury', 'mercury', '#89d672'),
        ('Jupiter', 'jupiter', '#ffbb5c'),
        ('Venus', 'venus', '#f29bff'),
        ('Saturn', 'saturn', '#63b3ed'),
        ('Rahu', 'rahu', '#63b3ed'),
        ('Ketu', 'ketu', '#63b3ed'),
    ]
    
    for idx, (display_name, key, color) in enumerate(planets_order):
        planet_data = chart.get(key, {})
        if not planet_data: continue
        
        # Grid line
        draw.line([(0, y+40), (width, y+40)], fill='#333333', width=1)
        
        # Name
        draw.text((x_positions[0], y+20), display_name, fill=color, font=text_font, anchor="lm")
        
        # Karaka
        draw.text((x_positions[1], y+20), planet_data.get('karaka', '-'), fill='#ffffff', font=text_font, anchor="lm")
        
        # Degrees
        deg = planet_data.get('degree', 0)
        minutes = int((deg % 1) * 60)
        seconds = int(((deg % 1) * 60 % 1) * 60)
        deg_str = f"{int(deg):02d}°{minutes:02d}'{seconds:02d}\""
        draw.text((x_positions[2], y+20), deg_str, fill='#ffffff', font=text_font, anchor="lm")
        
        # Rasi
        draw.text((x_positions[3], y+20), planet_data.get('sign', 'N/A'), fill='#6ebfb5', font=text_font, anchor="lm")
        
        # Navamsa (D9)
        d9_data = chart.get('d9_chart', {}).get(key, {})
        draw.text((x_positions[4], y+20), d9_data.get('sign', 'N/A'), fill='#6ebfb5', font=text_font, anchor="lm")
        
        # Nakshatra (Pada, Lord)
        nak_info = planet_data.get('nakshatra', {})
        nak_text = f"{nak_info.get('nakshatra', 'N/A')} ({nak_info.get('pada', 'N/A')}, {nak_info.get('lord', 'N/A')[:2]})"
        draw.text((x_positions[5], y+20), nak_text, fill='#6ebfb5', font=text_font, anchor="lm")
        
        # Relationship
        draw.text((x_positions[6], y+20), planet_data.get('relationship', 'Neutral'), fill='#ffffff', font=text_font, anchor="lm")
        
        # House
        draw.text((x_positions[7], y+20), str(planet_data.get('house', '-')), fill='#ffffff', font=text_font, anchor="lm")
        
        # Lord
        draw.text((x_positions[8], y+20), planet_data.get('rules_houses', '-'), fill='#ffffff', font=text_font, anchor="lm")
        
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

    chart = generate_vedic_chart(name, year, month, day, hour, minute, place_name, lat, lon)
    
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
                
                with gr.Tab("💍 D9 - Navamsa"):
                    d9_chart = gr.Image(label="D9 Marriage Chart", height=500)
                
                with gr.Tab("💼 D10 - Dasamsa"):
                    d10_chart = gr.Image(label="D10 Career Chart", height=500)
                
                with gr.Tab("👨‍👩‍👧 D12 - Dwadasamsa"):
                    d12_chart = gr.Image(label="D12 Family Chart", height=500)
        
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
                """Extract text and suggestions from AI response"""
                if "[SUGGESTIONS]" in response:
                    parts = response.split("[SUGGESTIONS]")
                    text = parts[0].strip()
                    sug_raw = parts[1].replace("\n", ",").split(",")
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
        [chart_summary, planetary_table_img, nakshatra_detailed_img, d1_chart, d9_chart, d10_chart, d12_chart, chart_state]
    )


if __name__ == "__main__":
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860)
