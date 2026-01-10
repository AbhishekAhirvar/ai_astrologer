
from backend.schemas import CompleteDashaInfo, DashaPeriod
from datetime import datetime
import swisseph as swe

def jd_to_str(jd: float) -> str:
    try:
        y, m, d, h = swe.revjul(jd)
        return f"{y:04d}-{m:02d}-{d:02d}"
    except:
        return ""

def create_dasha_html(dasha_info: CompleteDashaInfo) -> str:
    """
    Generate rich HTML representation of Dasha Analysis.
    """
    if not dasha_info:
        return "<p>No Dasha Data Available</p>"
        
    state = dasha_info.current_state
    
    # 1. Current Period Hierarchy
    html = """
    <div style="font-family: sans-serif; padding: 10px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9;">
        <h3 style="color: #2c3e50;">Current Time - Vimshottari Dasha Data</h3>
        <table style="width:100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background:#ecf0f1; color:#2c3e50;">
                <th style="padding:8px; text-align:left;">Level</th>
                <th style="padding:8px; text-align:left;">Lord</th>
                <th style="padding:8px; text-align:left;">End Date (Approx)</th>
                <th style="padding:8px; text-align:left;">Balance (Years)</th>
            </tr>
    """
    
    levels = [
        ('Maha Dasha', state.maha_dasha),
        ('Antar Dasha', state.antar_dasha),
        ('Pratyantar', state.pratyantar_dasha),
        ('Sookshma', state.sookshma_dasha),
        ('Prana', state.prana_dasha)
    ]
    
    for label, p in levels:
        if p:
            end_date = jd_to_str(p.end_jd)
            bal = f"{p.duration_years:.3f}" if p.duration_years else "-"
            extra_style = "font-weight:bold;" if label == 'Maha Dasha' else ""
            
            html += f"""
            <tr style="border-bottom: 1px solid #eee; {extra_style}">
                <td style="padding:8px;">{label}</td>
                <td style="padding:8px; color: #e74c3c;">{p.lord}</td>
                <td style="padding:8px;">{end_date}</td>
                <td style="padding:8px;">{bal}</td>
            </tr>
            """
            
    html += "</table>"
    
    # 2. 120 Year Timeline Summary
    html += """
        <h3 style="color: #2c3e50;">120-Year Cycle Overview</h3>
        <div style="max-height: 300px; overflow-y: auto;">
        <table style="width:100%; border-collapse: collapse;">
            <tr style="background:#ecf0f1; color:#2c3e50;">
                <th style="padding:5px;">Maha Dasha</th>
                <th style="padding:5px;">Duration</th>
                <th style="padding:5px;">Start</th>
                <th style="padding:5px;">End</th>
            </tr>
    """
    
    for p in dasha_info.timeline:
        s_date = jd_to_str(p.start_jd)
        e_date = jd_to_str(p.end_jd)
        html += f"""
            <tr style="border-bottom: 1px solid #eee; font-size: 0.9em;">
                <td style="padding:5px;"><b>{p.lord}</b></td>
                <td style="padding:5px;">{p.duration_years:.1f} Y</td>
                <td style="padding:5px;">{s_date}</td>
                <td style="padding:5px;">{e_date}</td>
            </tr>
        """
        
    html += """
        </table>
        </div>
    </div>
    """
    
    return html
