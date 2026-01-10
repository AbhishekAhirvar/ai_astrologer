
import matplotlib.pyplot as plt
import numpy as np
import os
from backend.logger import logger
from backend.schemas import ChartResponse, ShadbalaData

def create_shadbala_plots(chart: ChartResponse, output_dir: str, shadbala_data: dict = None):
    """
    Generate Shadbala visualizations: Bar Chart and Radar Chart.
    Returns tuple of paths: (bar_chart_path, radar_chart_path)
    
    Args:
        chart: ChartResponse object
        output_dir: Directory to save plots
        shadbala_data: Optional dict of {planet: strength}. If None, uses chart.shadbala
    """
    # Use provided shadbala_data or fall back to chart.shadbala
    if shadbala_data:
        totals = shadbala_data
    elif chart.shadbala and chart.shadbala.total_shadbala:
        totals = chart.shadbala.total_shadbala
    else:
        return None, None
        
    # Sort planets standard order or strength? 
    # Standard: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
    order = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    
    values = []
    labels = []
    colors = []
    
    # Minimum requirements (Virupas) - Standard
    # Sun: 390 (6.5 Rupa), Moon: 360, Mars: 300, Merc: 420, Jup: 390, Ven: 330, Sat: 300
    min_reqs = {
        'Sun': 390, 'Moon': 360, 'Mars': 300, 
        'Mercury': 420, 'Jupiter': 390, 'Venus': 330, 'Saturn': 300
    }
    
    for p in order:
        val = totals.get(p, 0.0)
        req = min_reqs.get(p, 300)
        values.append(val)
        labels.append(p)
        # Green if strong, Red if weak
        colors.append('#2ecc71' if val >= req else '#e74c3c')

    timestamp = int(os.path.getmtime(output_dir) if os.path.exists(output_dir) else 0)
    # Use random hash or timestamp to avoid cache collision? Logic in app calls this uniquely?
    # App passes output_dir. We should generate unique filename.
    # Actually app.py handles cleanup.
    
    bar_path = os.path.join(output_dir, f"shadbala_bar_{chart.metadata.name.replace(' ', '_')}.png")
    radar_path = os.path.join(output_dir, f"shadbala_radar_{chart.metadata.name.replace(' ', '_')}.png")
    
    # 1. Bar Chart
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, values, color=colors)
    plt.axhline(y=350, color='gray', linestyle='--', alpha=0.5, label='Avg Requirement') # Approx
    
    # Add Minimum Required Markers
    for i, p in enumerate(labels):
        req = min_reqs[p]
        plt.hlines(y=req, xmin=i-0.4, xmax=i+0.4, colors='black', linestyles='solid', linewidth=2)
        plt.text(i, values[i] + 10, f"{int(values[i])}", ha='center')
    
    plt.title("Shadbala Strength (Virupas)")
    plt.ylabel("Strength")
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(bar_path)
    plt.close()
    
    # 2. Radar Chart (Optional - Standardizing range 0 to 600)
    # ... Simplified for now to just Bar Chart as primary.
    # Radar charts are mathematically misleading for linear strength comparison 
    # but look good.
    
    return bar_path, None
