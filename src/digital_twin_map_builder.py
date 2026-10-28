"""
Intersection Digital Twin Map Builder
======================================
Generates a precise geometric representation of the intersections, 
color-coded by Level of Service (LOS) with rich engineering popups.
"""

import pandas as pd
import folium
from folium import plugins
import os

class DigitalTwinBuilder:
    def __init__(self):
        self.metrics_path = 'data/processed/approach_engineering_metrics.csv'
        self.output_path = 'outputs/intersection_digital_twin.html'
        
        # Define the geometric layout of our intersections [lat, lon]
        self.intersection_layouts = {
            'INT_01_Signalized': {
                'name': 'CG Road Signalized Intersection',
                'center': [23.0225, 72.5714],
                'approaches': {
                    'North': [[23.0245, 72.5714], [23.0227, 72.5714]], 
                    'South': [[23.0205, 72.5714], [23.0223, 72.5714]],
                    'East':  [[23.0225, 72.5734], [23.0225, 72.5716]],
                    'West':  [[23.0225, 72.5694], [23.0225, 72.5712]]
                }
            },
            'INT_02_Roundabout': {
                'name': 'Science City Roundabout',
                'center': [23.0350, 72.5650],
                'approaches': {
                    'North': [[23.0370, 72.5650], [23.0352, 72.5650]],
                    'South': [[23.0330, 72.5650], [23.0348, 72.5650]],
                    'East':  [[23.0350, 72.5670], [23.0350, 72.5652]]
                }
            }
        }

    def load_data(self):
        print("📊 Loading engineering metrics...")
        self.metrics_df = pd.read_csv(self.metrics_path)
        print(f"  Loaded metrics for {len(self.metrics_df)} approaches.")

    def get_los_color(self, los):
        colors = {'A': '#2ecc71', 'B': '#27ae60', 'C': '#f1c40f', 'D': '#e67e22', 'E': '#e74c3c', 'F': '#8e44ad'}
        return colors.get(los, '#95a5a6')

    def build_digital_twin(self):
        print("🏗️ Building Intersection Digital Twin...")
        
        esri_tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}'
        m = folium.Map(location=[23.028, 72.568], zoom_start=16, tiles=esri_tiles, attr='Esri')
        
        plugins.Fullscreen().add_to(m)
        
        title_html = '''
        <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%); width: 60%; z-index: 9999;">
            <h3 align="center" style="font-size:18px; background-color: rgba(255,255,255,0.95); padding:12px; border-radius:6px; box-shadow: 0 4px 8px rgba(0,0,0,0.15); margin: 0; font-family: 'Segoe UI', Arial, sans-serif;">
                <b>Intersection Digital Twin: LOS & TMC Analysis</b><br>
                <span style="font-size:13px; color:#555;">Click on any approach leg to view Level of Service, V/C Ratio, and Turning Movement Counts.</span>
            </h3>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))

        # Iterate through intersections and approaches
        for int_id, layout in self.intersection_layouts.items():
            for approach_name, coords in layout['approaches'].items():
                # Get metrics for this specific approach
                row = self.metrics_df[(self.metrics_df['intersection_id'] == int_id) & (self.metrics_df['approach_leg'] == approach_name)]
                
                if row.empty:
                    continue
                    
                row = row.iloc[0]
                los = row['los']
                color = self.get_los_color(los)
                
                # Build the rich engineering popup
                popup_html = f"""
                <div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; min-width: 220px; color: #333;">
                    <h4 style="margin: 0 0 8px 0; color: #2c3e50; border-bottom: 2px solid {color}; padding-bottom: 4px;">
                        📍 {layout['name']}<br>
                        <span style="font-size: 12px; color: #7f8c8d;">{approach_name}bound Approach</span>
                    </h4>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 8px;">
                        <tr>
                            <td style="padding: 4px 0; color: #555;">Level of Service:</td>
                            <td style="padding: 4px 0; font-weight: bold; text-align: right; color: {color}; font-size: 15px;">{los}</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0; color: #555;">V/C Ratio:</td>
                            <td style="padding: 4px 0; font-weight: bold; text-align: right;">{row['vc_ratio']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0; color: #555;">Peak Hour Vol:</td>
                            <td style="padding: 4px 0; font-weight: bold; text-align: right;">{row['avg_peak_hour_volume']:,.0f} veh/hr</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0; color: #555;">Peak Hour Factor:</td>
                            <td style="padding: 4px 0; font-weight: bold; text-align: right;">{row['phf']}</td>
                        </tr>
                    </table>
                    
                    <b style="font-size: 12px; color: #2c3e50;">Turning Movement Counts (Avg Hr):</b>
                    <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                        <tr>
                            <td style="padding: 2px 0;">Left Turn:</td>
                            <td style="padding: 2px 0; font-weight: bold; text-align: right;">{row.get('Left', 0):,.0f}</td>
                            <td style="padding: 2px 0;">Through:</td>
                            <td style="padding: 2px 0; font-weight: bold; text-align: right;">{row.get('Through', 0):,.0f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 2px 0;">Right Turn:</td>
                            <td style="padding: 2px 0; font-weight: bold; text-align: right;">{row.get('Right', 0):,.0f}</td>
                            <td style="padding: 2px 0;"></td>
                            <td style="padding: 2px 0;"></td>
                        </tr>
                    </table>
                </div>
                """
                
                # CRITICAL FIX: Use folium.PolyLine instead of GeoJson for raw coordinate lists
                folium.PolyLine(
                    locations=coords,
                    color=color,
                    weight=12, # Very thick so it's easily clickable
                    opacity=0.9,
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{approach_name}bound - LOS {los}"
                ).add_to(m)

        # Legend
        legend_html = '''
        <div style="position: fixed; bottom: 30px; right: 30px; width: 180px; background-color: rgba(255,255,255,0.95); border:1px solid #ccc; z-index:9999; font-family: 'Segoe UI', Arial, sans-serif; font-size:13px; padding: 12px; border-radius: 6px; box-shadow: 0 4px 8px rgba(0,0,0,0.15);">
            <b style="font-size: 14px; color: #2c3e50;">Level of Service (LOS)</b><br><br>
            <i style="background:#2ecc71; width: 12px; height: 12px; display: inline-block; border-radius: 50%; vertical-align: middle;"></i> <span style="vertical-align: middle;">A / B (Free Flow)</span><br>
            <i style="background:#f1c40f; width: 12px; height: 12px; display: inline-block; border-radius: 50%; vertical-align: middle;"></i> <span style="vertical-align: middle;">C (Stable)</span><br>
            <i style="background:#e67e22; width: 12px; height: 12px; display: inline-block; border-radius: 50%; vertical-align: middle;"></i> <span style="vertical-align: middle;">D (Unstable)</span><br>
            <i style="background:#e74c3c; width: 12px; height: 12px; display: inline-block; border-radius: 50%; vertical-align: middle;"></i> <span style="vertical-align: middle;">E (Near Capacity)</span><br>
            <i style="background:#8e44ad; width: 12px; height: 12px; display: inline-block; border-radius: 50%; vertical-align: middle;"></i> <span style="vertical-align: middle;">F (Gridlock)</span>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        self.map_obj = m
        print("  Digital Twin built successfully.")

    def save_map(self):
        print(f"💾 Saving Digital Twin to {self.output_path}...")
        os.makedirs('outputs', exist_ok=True)
        self.map_obj.save(self.output_path)
        print("✅ Dashboard saved! Open in your browser.")

if __name__ == "__main__":
    builder = DigitalTwinBuilder()
    builder.load_data()
    builder.build_digital_twin()
    builder.save_map()