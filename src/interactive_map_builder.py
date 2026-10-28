"""
Scenario Comparison Traffic Dashboard
=======================================
Generates a highly interactive map with toggleable layers for 
Morning, Midday, and Evening traffic scenarios.
"""

import geopandas as gpd
import folium
from folium import plugins
import os

class ScenarioMapBuilder:
    def __init__(self):
        self.network_path = 'data/processed/scenario_road_network.geojson'
        self.zones_path = 'data/processed/pedestrian_conflict_zones.geojson'
        self.output_path = 'outputs/scenario_traffic_dashboard.html'
        
    def load_data(self):
        print("🗺️ Loading spatial data...")
        self.network_gdf = gpd.read_file(self.network_path)
        self.zones_gdf = gpd.read_file(self.zones_path)
        print(f"  Loaded {len(self.network_gdf)} segments.")

    def get_color(self, idx):
        if idx == 0: return '#95a5a6'
        elif idx <= 40: return '#2ecc71'
        elif idx <= 75: return '#f1c40f'
        else: return '#e74c3c'

    def build_scenario_map(self):
        print(" Building scenario comparison map...")
        
        esri_tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}'
        m = folium.Map(location=[23.028, 72.568], zoom_start=15, tiles=esri_tiles, attr='Esri')
        
        plugins.Fullscreen().add_to(m)
        
        # Title
        title_html = '''
        <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%); width: 60%; z-index: 9999;">
            <h3 align="center" style="font-size:18px; background-color: rgba(255,255,255,0.95); padding:12px; border-radius:6px; box-shadow: 0 4px 8px rgba(0,0,0,0.15); margin: 0; font-family: 'Segoe UI', Arial, sans-serif;">
                <b>Ahmedabad Smart City: Scenario Comparison</b><br>
                <span style="font-size:13px; color:#555;">Toggle layers in the top-right to compare Morning, Midday, and Evening Peak.</span>
            </h3>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))

        # Define our 3 scenarios
        scenarios = [
            {'name': 'Morning Peak (09:00)', 'vol_col': 'vol_09', 'idx_col': 'idx_09', 'time': '09:00 AM'},
            {'name': 'Midday Off-Peak (14:00)', 'vol_col': 'vol_14', 'idx_col': 'idx_14', 'time': '02:00 PM'},
            {'name': 'Evening Peak (19:00)', 'vol_col': 'vol_19', 'idx_col': 'idx_19', 'time': '07:00 PM'}
        ]

        # Create a Feature Group for each scenario
        for scenario in scenarios:
            fg = folium.FeatureGroup(name=scenario['name'], show=(scenario['name'] == 'Evening Peak (19:00)')) # Show evening by default
            
            for _, row in self.network_gdf.iterrows():
                vol = float(row[scenario['vol_col']])
                idx = float(row[scenario['idx_col']])
                
                if vol == 0:
                    continue # Skip roads with no traffic for this scenario to keep map clean
                    
                color = self.get_color(idx)
                
                # RICH HTML POPUP
                popup_html = f"""
                <div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; min-width: 200px; color: #333;">
                    <h4 style="margin: 0 0 8px 0; color: #2c3e50; border-bottom: 2px solid {color}; padding-bottom: 4px;">
                        📍 {row.get('intersection_name', 'Unknown')}<br>
                        <span style="font-size: 12px; color: #7f8c8d;">{scenario['time']}</span>
                    </h4>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 4px 0; color: #555;">Hourly Volume:</td>
                            <td style="padding: 4px 0; font-weight: bold; text-align: right;">{vol:,.0f} <span style="font-size:11px;">veh/hr</span></td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0; color: #555;">Congestion Index:</td>
                            <td style="padding: 4px 0; font-weight: bold; text-align: right; color: {color};">{idx:.1f} / 100</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0; color: #555;">Level of Service:</td>
                            <td style="padding: 4px 0; font-weight: bold; text-align: right;">{'F (Gridlock)' if idx > 90 else 'D (Unstable)' if idx > 75 else 'C (Stable)' if idx > 50 else 'B (Good)'}</td>
                        </tr>
                    </table>
                </div>
                """
                
                folium.GeoJson(
                    row['geometry'],
                    style_function=lambda x, c=color: {
                        'color': c,
                        'weight': 6, # Thick lines so they are clearly visible
                        'opacity': 0.9
                    },
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{row.get('intersection_name', 'Road')} - {scenario['time']}"
                ).add_to(fg)
                
            fg.add_to(m)

        # Add Pedestrian Conflict Zones (Always visible)
        conflict_fg = folium.FeatureGroup(name="⚠️ Pedestrian Conflict Zones", show=True)
        for _, row in self.zones_gdf.iterrows():
            folium.GeoJson(
                row['geometry'],
                style_function=lambda x: {
                    'fillColor': '#e74c3c',
                    'color': '#c0392b',
                    'weight': 2,
                    'fillOpacity': 0.35
                },
                tooltip=f"<b>⚠️ Pedestrian Conflict Zone</b><br>{row['intersection_name']}"
            ).add_to(conflict_fg)
        conflict_fg.add_to(m)

        # Add Layer Control
        folium.LayerControl(collapsed=False).add_to(m)

        # Legend
        legend_html = '''
        <div style="position: fixed; bottom: 30px; right: 30px; width: 180px; background-color: rgba(255,255,255,0.95); border:1px solid #ccc; z-index:9999; font-family: 'Segoe UI', Arial, sans-serif; font-size:13px; padding: 12px; border-radius: 6px; box-shadow: 0 4px 8px rgba(0,0,0,0.15);">
            <b style="font-size: 14px; color: #2c3e50;">Congestion Level</b><br><br>
            <i style="background:#e74c3c; width: 12px; height: 12px; display: inline-block; border-radius: 50%; vertical-align: middle;"></i> <span style="vertical-align: middle;">High (>75)</span><br>
            <i style="background:#f1c40f; width: 12px; height: 12px; display: inline-block; border-radius: 50%; vertical-align: middle;"></i> <span style="vertical-align: middle;">Medium (40-75)</span><br>
            <i style="background:#2ecc71; width: 12px; height: 12px; display: inline-block; border-radius: 50%; vertical-align: middle;"></i> <span style="vertical-align: middle;">Low (<40)</span><br>
            <hr style="margin: 8px 0; border: 0; border-top: 1px solid #ccc;">
            <i style="background:#e74c3c; width: 12px; height: 12px; display: inline-block; border-radius: 50%; vertical-align: middle; opacity: 0.4;"></i> <span style="vertical-align: middle;">Pedestrian Conflict</span>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        self.map_obj = m
        print("  Map built successfully with rich popups and layer control.")

    def save_map(self):
        print(f"💾 Saving dashboard to {self.output_path}...")
        os.makedirs('outputs', exist_ok=True)
        self.map_obj.save(self.output_path)
        print("✅ Dashboard saved! Open in your browser.")

if __name__ == "__main__":
    builder = ScenarioMapBuilder()
    builder.load_data()
    builder.build_scenario_map()
    builder.save_map()