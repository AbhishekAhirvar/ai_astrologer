import gradio as gr
import asyncio
import hashlib
from backend.location import get_location_data
from backend.astrology import generate_vedic_chart
from backend.ai import get_astrology_prediction_stream, get_followup_questions
from backend.chart_renderer import generate_all_charts, generate_single_varga, get_chart_json
from backend.shadbala_renderer import create_shadbala_plots
from backend.dasha_renderer import create_dasha_html

from backend.table_renderer import create_planetary_table_image, create_detailed_nakshatra_table
from backend.logger import logger
import time
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

# Table generation logic moved to backend.table_renderer

user_requests = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 10
CHARTS_DIR = "./generated_charts"
REPORT_CACHE = {}

def get_report_cache_key(name, dob, tob, place):
    return hashlib.md5(f"{name}{dob}{tob}{place}".encode()).hexdigest()

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

async def generate_report(name, gender, dob_date, dob_time, place_name):
    """Generate birth chart with all tables (Async + Cached)"""
    if not all([name, dob_date, dob_time, place_name]):
        return "⚠️ All fields are required!", None, None, None, None, None, None, None
    
    cache_key = get_report_cache_key(name, dob_date, dob_time, place_name)
    if cache_key in REPORT_CACHE:
        # Validate cache: check if file paths still exist (important for HF Spaces)
        cached_result = REPORT_CACHE[cache_key]
        # cached_result = (summary_text, table_path, nak_table_path, d1_img, chart, d9_img, shadbala_img, dasha_html_content)
        files_to_check = [cached_result[1], cached_result[2], cached_result[3], cached_result[5], cached_result[6]]
        files_exist = all(f and os.path.exists(f) for f in files_to_check if f)
        
        if files_exist:
            logger.info(f"Serving report from cache for {name}")
            return cached_result
        else:
            logger.warning(f"Cache invalidated for {name} - files no longer exist")
            del REPORT_CACHE[cache_key]  # Remove stale cache

    logger.info(f"Generating report for: {name} ({dob_date} {dob_time}) at {place_name}")
    cleanup_old_charts(CHARTS_DIR)

    try:
        # Date parsing logic (kept same as before but inside async)
        dob_dt = None
        formats_to_try = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d%m%Y", "%Y%m%d"]
        clean_date = dob_date.strip()
        for fmt in formats_to_try:
            try:
                dob_dt = datetime.strptime(clean_date, fmt)
                break
            except ValueError: continue
        if not dob_dt: return "❌ Invalid Date format.", None, None, None, None, None, None, None
        year, month, day = dob_dt.year, dob_dt.month, dob_dt.day
        dob_date = dob_dt.strftime("%Y-%m-%d")

        # Time parsing
        time_parts = dob_time.split(":")
        hour, minute = int(time_parts[0]), int(time_parts[1])
        
        # Async Location Lookup
        loc_data = await get_location_data(place_name)
        if not loc_data:
            return f"❌ Location '{place_name}' not found.", None, None, None, None, None, None, None
        lat, lon, address = loc_data

        # Blocking chart gen in thread (Enable All Features)
        chart = await asyncio.to_thread(
            generate_vedic_chart, 
            name, year, month, day, hour, minute, place_name, 
            lat, lon, "Asia/Kolkata"
        )
        if hasattr(chart, 'metadata'): chart.metadata.gender = gender
        elif '_metadata' in chart: chart['_metadata']['gender'] = gender
        
        # Blocking chart rendering
        chart_images = await asyncio.to_thread(generate_all_charts, chart, person_name=name, output_dir=CHARTS_DIR)
        
        timestamp = int(time.time())
        table_path = os.path.join(CHARTS_DIR, f"{name}_planetary_table_{timestamp}.png")
        nak_table_path = os.path.join(CHARTS_DIR, f"{name}_nakshatra_detailed_{timestamp}.png")
        
        await asyncio.to_thread(create_planetary_table_image, chart, table_path)
        await asyncio.to_thread(create_detailed_nakshatra_table, chart, nak_table_path)

        # New Visualizations - Generate on-the-fly
        from backend.shadbala import calculate_shadbala_for_chart
        from backend.dasha_system import VimshottariDashaSystem
        import pytz
        import swisseph as swe
        
        # Calculate Shadbala
        shadbala_data = await asyncio.to_thread(calculate_shadbala_for_chart, chart)
        shadbala_img, _ = await asyncio.to_thread(create_shadbala_plots, chart, CHARTS_DIR, shadbala_data)
        
        # Calculate Complete Dasha
        dasha_sys = VimshottariDashaSystem()
        now_utc = datetime.now(pytz.UTC)
        cur_jd = swe.julday(now_utc.year, now_utc.month, now_utc.day, now_utc.hour + now_utc.minute/60.0)
        birth_jd = swe.julday(year, month, day, hour + minute/60.0)
        moon_pos = chart.planets['moon'].abs_pos
        complete_dasha = await asyncio.to_thread(dasha_sys.calculate_complete_dasha, moon_pos, birth_jd, cur_jd)
        dasha_html_content = await asyncio.to_thread(create_dasha_html, complete_dasha)

        # Summary Text
        if hasattr(chart, 'planets'):
            moon_data = chart.planets.get('moon')
            moon_naks = moon_data.nakshatra if moon_data and hasattr(moon_data, 'nakshatra') else {}
            metadata = chart.metadata
            name_val = getattr(metadata, 'name', 'User')
        else: # Dict fallback
            moon_naks = chart['moon'].get('nakshatra', {})
            metadata = chart.get('_metadata', {})
            name_val = metadata.get('name', 'User')

        summary_text = f"## 🌟 Birth Chart: {name_val}\n**👤 Gender:** {gender}\n**📍 Location:** {address}\n**📅 Date/Time:** {dob_date} at {dob_time}\n---\n### 🌙 MOON NAKSHATRA\n**Nakshatra:** {getattr(moon_naks, 'nakshatra', 'N/A')}\n**Lord:** {getattr(moon_naks, 'lord', 'N/A')}"
        
        d1_img = chart_images.get('D1')
        
        # Pre-generate D9 for faster initial display
        chart_json = get_chart_json(chart)
        d9_img = await asyncio.to_thread(generate_single_varga, chart_json, "D9", person_name=name_val, output_dir=CHARTS_DIR)
        
        result = (summary_text, table_path, nak_table_path, d1_img, chart, d9_img, shadbala_img, dasha_html_content)
        REPORT_CACHE[cache_key] = result
        return result

    except Exception as e:
        logger.exception(f"Error in generate_report: {e}")
        return f"⚠️ Error: {str(e)}", None, None, None, None, None, None, None

def update_varga_display(chart_data, varga_type):
    """Update varga chart image based on dropdown selection"""
    if not chart_data:
        return None
    
    # Map label to chart key
    mapping = {
        "D1 Rasi": "D1", "Moon Chart": "Moon", "Sun Chart": "Sun", "Arudha Lagna": "Arudha"
    }
    
    chart_code = mapping.get(varga_type)
    if not chart_code:
        # Extract D number from string like "D9 Navamsa" -> "D9"
        chart_code = varga_type.split(' ')[0]
    
    # Handle object or dict
    if hasattr(chart_data, 'metadata'):
        name = getattr(chart_data.metadata, 'name', 'User')
    else:
        name = chart_data.get('_metadata', {}).get('name', 'User')
    
    chart_json = get_chart_json(chart_data)
    img_path = generate_single_varga(chart_json, chart_code, person_name=name, output_dir=CHARTS_DIR)
    return img_path



# Custom CSS for proper textbox rendering
custom_css = """
th, td {
    padding: 8px !important; 
}
"""

with gr.Blocks(title="Vedic Astrology AI", fill_height=False) as demo:
    
    chart_state = gr.State(None)
    
    gr.HTML("""
    <div style='text-align: center; padding: 20px;'>
        <h1>🌟 Vedic Astrology AI</h1>
        <p>Birth Charts • Nakshatras • Divisional Charts • AI Predictions</p>
        <p style='font-size: 12px; color: #666;'>Powered by OpenAI GPT-5.2 (2026 Responses API)</p>
    </div>
    """)
    
    with gr.Tabs():
        
        # TAB 1: Chart Generator
        with gr.Tab("📊 Birth Chart Generator"):
            gr.Markdown("### Enter Birth Details")
            
            with gr.Group():
                with gr.Row():
                    name = gr.Textbox(label="Name", placeholder="John Doe", scale=2)
                    gender = gr.Radio(["Male", "Female", "Other"], label="Gender", value="Male", scale=1)
                
                with gr.Row():
                    dob_date = gr.Textbox(label="Birth Date", placeholder="YYYY-MM-DD", value=datetime.now().strftime("%Y-%m-%d"))
                    dob_time = gr.Textbox(label="Birth Time", placeholder="HH:MM", value=datetime.now().strftime("%H:%M"))
                
                place_name = gr.Textbox(label="Birth Place", placeholder="New Delhi, India", value="New Delhi")
            
            generate_btn = gr.Button("🔮 Generate Chart", variant="primary", size="lg")
            
            chart_summary = gr.Markdown()
            
            # Charts in TABS
            with gr.Tabs():
                with gr.Tab("📋 Planetary Positions"):
                    planetary_table_img = gr.Image(label="Planetary Positions Table", height=450)
                
                with gr.Tab("🌙 Nakshatra Analysis"):
                    nakshatra_detailed_img = gr.Image(label="Detailed Nakshatra Analysis", height=500)
                
                with gr.Tab("🎯 D1 - Rasi Chart"):
                    d1_chart = gr.Image(label="D1 Birth Chart", height=500)
                
                with gr.Tab("💪 Shadbala Strength"):
                    shadbala_chart_img = gr.Image(label="Shadbala Bar Chart", height=500)
                    
                with gr.Tab("⏳ Dasha Timeline"):
                    dasha_html = gr.HTML(label="Vimshottari Dasha Analysis")
                
                with gr.Tab("💠 Divisional Charts (Vargas)"):
                    with gr.Group():
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
            # Bot Mode Selector
            gr.Markdown("### 🤖 AI Mode Selection")
            with gr.Group():
                vedic_bot_mode = gr.Radio(
                    choices=["PRO (Accuracy)", "LITE (Tokens)", "LEGACY (Classic)"],
                    value="PRO (Accuracy)",
                    label="Bot Mode",
                    info="PRO: Maximum accuracy | LITE: Token-optimized | LEGACY: Classic behavior"
                )
                vedic_model_select = gr.Dropdown(
                    choices=["gpt-5-nano", "gpt-5-mini"],
                    value="gpt-5-nano",
                    label="Model",
                    info="Select model"
                )
            
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
                    
                    with gr.Group():
                        v_msg = gr.Textbox(label="Ask Vedic Astrology", placeholder="Ask any question about your life...", scale=7)

        # TAB 3: KP AI Chat
        with gr.Tab("🧭 KP AI Chat"):
            # Bot Mode Selector
            gr.Markdown("### 🤖 AI Mode Selection")
            with gr.Group():
                kp_bot_mode = gr.Radio(
                    choices=["PRO (Accuracy)", "LITE (Tokens)", "LEGACY (Classic)"],
                    value="PRO (Accuracy)",
                    label="Bot Mode",
                    info="PRO: Maximum accuracy | LITE: Token-optimized | LEGACY: Classic behavior"
                )
                kp_model_select = gr.Dropdown(
                    choices=["gpt-5-nano", "gpt-5-mini"],
                    value="gpt-5-nano",
                    label="Model",
                    info="Select model"
                )
            
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
                    
                    with gr.Group():
                        kp_msg = gr.Textbox(label="Ask KP Astrology", placeholder="Ask using Krishnamurti Paddhati rules...", scale=7)


    async def handle_chat_input(user_input, history, chart_data, is_kp=False, bot_mode_ui="PRO (Accuracy)", model="gpt-5-nano"):
        """Unified chat entry point with streaming and memory"""
        if not chart_data:
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": "⚠️ Please generate a birth chart first!"})
            yield history, "", gr.Button(visible=False), gr.Button(visible=False), gr.Button(visible=False)
            return
        
        if not check_rate_limit():
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": "⚠️ Rate limit exceeded."})
            yield history, "", gr.Button(visible=False), gr.Button(visible=False), gr.Button(visible=False)
            return
        
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            api_key = api_key.strip()
        
        # Parse bot mode from UI
        if "LITE" in bot_mode_ui:
            bot_mode = "lite"
        elif "LEGACY" in bot_mode_ui:
            bot_mode = "legacy"
        else:  # PRO
            bot_mode = "pro"
        
        # Setup UI
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": ""})
        yield history, "", gr.Button(visible=False), gr.Button(visible=False), gr.Button(visible=False)

        # 1. Stream Prediction and Fetch Suggestions in Parallel
        try:
            # Use legacy mode if selected (with custom system instruction)
            if bot_mode == "legacy":
                from backend.ai import OMKAR_SYSTEM_INSTRUCTION_V2, OMKAR_SYSTEM_INSTRUCTION
                system_instr = OMKAR_SYSTEM_INSTRUCTION_V2 if is_kp else OMKAR_SYSTEM_INSTRUCTION
                stream_gen = get_astrology_prediction_stream(
                    chart_data, user_input, api_key=api_key, history=history[:-2], 
                    is_kp_mode=is_kp, system_instruction=system_instr, model=model
                )
            else:
                # Use new 4-bot system
                stream_gen = get_astrology_prediction_stream(
                    chart_data, user_input, api_key=api_key, history=history[:-2], 
                    is_kp_mode=is_kp, bot_mode=bot_mode, model=model
                )
            sug_task = asyncio.create_task(get_followup_questions(api_key=api_key, chart_data=chart_data, is_kp_mode=is_kp, history=history))

            full_text = ""
            async for chunk in stream_gen:
                full_text += chunk
                history[-1]["content"] = full_text
                yield history, "", gr.Button(visible=False), gr.Button(visible=False), gr.Button(visible=False)
        except Exception as e:
            logger.error(f"Stream error: {e}")
            history[-1]["content"] = f"⚠️ AI Error: {str(e)}. Please check your quota or try again later."
            yield history, "", gr.Button(visible=False), gr.Button(visible=False), gr.Button(visible=False)
            return

        # 2. Update Suggestions after stream finishes
        try:
            suggestions = await sug_task
        except Exception as e:
            logger.error(f"Suggestions error: {e}")
            suggestions = ["What does this mean?", "Any remedies?", "Future outlook?"]

        yield history, "", gr.Button(value=suggestions[0], visible=True), gr.Button(value=suggestions[1], visible=True), gr.Button(value=suggestions[2], visible=True)

    # Wrappers
    async def vedic_chat_handler(u, h, c, bm, m):
        async for res in handle_chat_input(u, h, c, False, bm, m):
            yield res

    async def kp_chat_handler(u, h, c, bm, m):
        async for res in handle_chat_input(u, h, c, True, bm, m):
            yield res

    # VEDIC EVENTS
    v_msg.submit(
        vedic_chat_handler,
        [v_msg, v_chatbot, chart_state, vedic_bot_mode, vedic_model_select], 
        [v_chatbot, v_msg, v_s_btn1, v_s_btn2, v_s_btn3]
    )
    for qb in vedic_q_btns:
        qb.click(
            vedic_chat_handler,
            [qb, v_chatbot, chart_state, vedic_bot_mode, vedic_model_select],
            [v_chatbot, v_msg, v_s_btn1, v_s_btn2, v_s_btn3]
        )
    for sb in [v_s_btn1, v_s_btn2, v_s_btn3]:
        sb.click(
            vedic_chat_handler,
            [sb, v_chatbot, chart_state, vedic_bot_mode, vedic_model_select],
            [v_chatbot, v_msg, v_s_btn1, v_s_btn2, v_s_btn3]
        )

    # KP EVENTS
    kp_msg.submit(
        kp_chat_handler,
        [kp_msg, kp_chatbot, chart_state, kp_bot_mode, kp_model_select], 
        [kp_chatbot, kp_msg, kp_s_btn1, kp_s_btn2, kp_s_btn3]
    )
    for qb in kp_q_btns:
        qb.click(
            kp_chat_handler,
            [qb, kp_chatbot, chart_state, kp_bot_mode, kp_model_select],
            [kp_chatbot, kp_msg, kp_s_btn1, kp_s_btn2, kp_s_btn3]
        )
    for sb in [kp_s_btn1, kp_s_btn2, kp_s_btn3]:
        sb.click(
            kp_chat_handler,
            [sb, kp_chatbot, chart_state, kp_bot_mode, kp_model_select],
            [kp_chatbot, kp_msg, kp_s_btn1, kp_s_btn2, kp_s_btn3]
        )
    
    # Wire generate button
    generate_btn.click(
        generate_report,
        [name, gender, dob_date, dob_time, place_name],
        [chart_summary, planetary_table_img, nakshatra_detailed_img, d1_chart, chart_state, varga_chart_img, shadbala_chart_img, dasha_html],
        show_progress="minimal"
    )
    
    # Update varga on dropdown change
    varga_select.change(
        update_varga_display,
        [chart_state, varga_select],
        [varga_chart_img]
    )


if __name__ == "__main__":
    # Clear cache and old files on startup (important for HF Spaces)
    REPORT_CACHE.clear()
    cleanup_old_charts(CHARTS_DIR)
    logger.info("App starting - cache cleared")
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860, css=custom_css)
