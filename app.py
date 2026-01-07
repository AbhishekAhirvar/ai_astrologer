import gradio as gr
import asyncio
import hashlib
from backend.location import get_location_data
from backend.astrology import generate_vedic_chart
from backend.ai import get_astrology_prediction_stream, get_followup_questions
from backend.chart_renderer import generate_all_charts, generate_single_varga
from backend.table_renderer import create_planetary_table_image, create_detailed_nakshatra_table
from backend.logger import logger
import time
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

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

# Table generation logic moved to backend.table_renderer

async def generate_report(name, gender, dob_date, dob_time, place_name):
    """Generate birth chart with all tables (Async + Cached)"""
    if not all([name, dob_date, dob_time, place_name]):
        return "⚠️ All fields are required!", None, None, None, None, None
    
    cache_key = get_report_cache_key(name, dob_date, dob_time, place_name)
    if cache_key in REPORT_CACHE:
        logger.info(f"Serving report from cache for {name}")
        return REPORT_CACHE[cache_key]

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
        if not dob_dt: return "❌ Invalid Date format.", None, None, None, None
        year, month, day = dob_dt.year, dob_dt.month, dob_dt.day
        dob_date = dob_dt.strftime("%Y-%m-%d")

        # Time parsing
        time_parts = dob_time.split(":")
        hour, minute = int(time_parts[0]), int(time_parts[1])
        
        # Async Location Lookup
        loc_data = await get_location_data(place_name)
        if not loc_data:
            return f"❌ Location '{place_name}' not found.", None, None, None, None
        lat, lon, address = loc_data

        # Blocking chart gen in thread
        chart = await asyncio.to_thread(generate_vedic_chart, name, year, month, day, hour, minute, place_name, lat, lon)
        if '_metadata' in chart: chart['_metadata']['gender'] = gender
        
        # Blocking chart rendering in thread
        chart_images = await asyncio.to_thread(generate_all_charts, chart, person_name=name, output_dir=CHARTS_DIR)
        
        timestamp = int(time.time())
        table_path = os.path.join(CHARTS_DIR, f"{name}_planetary_table_{timestamp}.png")
        nak_table_path = os.path.join(CHARTS_DIR, f"{name}_nakshatra_detailed_{timestamp}.png")
        
        await asyncio.to_thread(create_planetary_table_image, chart, table_path)
        await asyncio.to_thread(create_detailed_nakshatra_table, chart, nak_table_path)

        if hasattr(chart, 'planets'):
            moon_data = chart.planets.get('moon')
            moon_naks = moon_data.nakshatra if moon_data and hasattr(moon_data, 'nakshatra') else {}
        else:
            moon_naks = chart['moon'].get('nakshatra', {})
        
        # Metadata access
        if hasattr(chart, 'metadata'):
            metadata = chart.metadata
            name_val = getattr(metadata, 'name', 'User')
        else:
            metadata = chart.get('_metadata', {})
            name_val = metadata.get('name', 'User')

        summary_text = f"## 🌟 Birth Chart: {name_val}\n**👤 Gender:** {gender}\n**📍 Location:** {address}\n**📅 Date/Time:** {dob_date} at {dob_time}\n---\n### 🌙 MOON NAKSHATRA\n**Nakshatra:** {getattr(moon_naks, 'nakshatra', 'N/A')}\n**Lord:** {getattr(moon_naks, 'lord', 'N/A')}"
        
        d1_img = chart_images.get('D1')
        
        # Pre-generate D9 for faster initial display
        d9_img = await asyncio.to_thread(generate_single_varga, chart, "D9", person_name=name_val, output_dir=CHARTS_DIR)
        
        result = (summary_text, table_path, nak_table_path, d1_img, chart, d9_img)
        REPORT_CACHE[cache_key] = result
        return result

    except Exception as e:
        logger.exception(f"Error in generate_report: {e}")
        return f"⚠️ Error: {str(e)}", None, None, None, None, None

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
    
    
    # Handle object or dict
    if hasattr(chart_data, 'metadata'):
        name = getattr(chart_data.metadata, 'name', 'User')
    else:
        name = chart_data.get('_metadata', {}).get('name', 'User')
        
    img_path = generate_single_varga(chart_data, chart_code, person_name=name, output_dir=CHARTS_DIR)
    return img_path



with gr.Blocks(title="Vedic Astrology AI") as demo:
    
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
            
            with gr.Row():
                name = gr.Textbox(label="Name", placeholder="John Doe", container=False)
                gender = gr.Radio(["Male", "Female", "Other"], label="Gender", value="Male")
            
            with gr.Row():
                dob_date = gr.Textbox(label="Birth Date", placeholder="YYYY-MM-DD", value=datetime.now().strftime("%Y-%m-%d"), container=False)
                dob_time = gr.Textbox(label="Birth Time", placeholder="HH:MM", value=datetime.now().strftime("%H:%M"), container=False)
            
            place_name = gr.Textbox(label="Birth Place", placeholder="New Delhi, India", value="New Delhi", container=False)
            
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



            async def handle_chat_input(user_input, history, chart_data, is_kp=False):
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
                
                # Setup UI
                history.append({"role": "user", "content": user_input})
                history.append({"role": "assistant", "content": ""})
                yield history, "", gr.Button(visible=False), gr.Button(visible=False), gr.Button(visible=False)

                # 1. Stream Prediction and Fetch Suggestions in Parallel
                try:
                    stream_gen = get_astrology_prediction_stream(chart_data, user_input, api_key=api_key, history=history[:-2], is_kp_mode=is_kp)
                    sug_task = asyncio.create_task(get_followup_questions(api_key=api_key, chart_data=chart_data, is_kp_mode=is_kp))

                    full_text = ""
                    async for chunk in stream_gen:
                        full_text += chunk
                        history[-1]["content"] = full_text
                        # Yield updates for all outputs to ensure rendering in Gradio 6
                        yield history, "", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
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

                s1 = gr.Button(suggestions[0], visible=True)
                s2 = gr.Button(suggestions[1], visible=True)
                s3 = gr.Button(suggestions[2], visible=True)
                yield history, "", s1, s2, s3

            # Wrappers
            async def vedic_chat_handler(u, h, c):
                async for res in handle_chat_input(u, h, c, False):
                    yield res

            async def kp_chat_handler(u, h, c):
                async for res in handle_chat_input(u, h, c, True):
                    yield res

            # VEDIC EVENTS
            v_msg.submit(
                vedic_chat_handler,
                [v_msg, v_chatbot, chart_state], 
                [v_chatbot, v_msg, v_s_btn1, v_s_btn2, v_s_btn3]
            )
            for qb in vedic_q_btns:
                qb.click(
                    vedic_chat_handler,
                    [qb, v_chatbot, chart_state],
                    [v_chatbot, v_msg, v_s_btn1, v_s_btn2, v_s_btn3]
                )
            for sb in [v_s_btn1, v_s_btn2, v_s_btn3]:
                sb.click(
                    vedic_chat_handler,
                    [sb, v_chatbot, chart_state],
                    [v_chatbot, v_msg, v_s_btn1, v_s_btn2, v_s_btn3]
                )

            # KP EVENTS
            kp_msg.submit(
                kp_chat_handler,
                [kp_msg, kp_chatbot, chart_state], 
                [kp_chatbot, kp_msg, kp_s_btn1, kp_s_btn2, kp_s_btn3]
            )
            for qb in kp_q_btns:
                qb.click(
                    kp_chat_handler,
                    [qb, kp_chatbot, chart_state],
                    [kp_chatbot, kp_msg, kp_s_btn1, kp_s_btn2, kp_s_btn3]
                )
            for sb in [kp_s_btn1, kp_s_btn2, kp_s_btn3]:
                sb.click(
                    kp_chat_handler,
                    [sb, kp_chatbot, chart_state],
                    [kp_chatbot, kp_msg, kp_s_btn1, kp_s_btn2, kp_s_btn3]
                )
    
    # Wire generate button
    generate_btn.click(
        generate_report,
        [name, gender, dob_date, dob_time, place_name],
        [chart_summary, planetary_table_img, nakshatra_detailed_img, d1_chart, chart_state, varga_chart_img],
        show_progress="minimal"
    )
    
    # Update varga on dropdown change
    varga_select.change(
        update_varga_display,
        [chart_state, varga_select],
        [varga_chart_img]
    )


if __name__ == "__main__":
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860)
