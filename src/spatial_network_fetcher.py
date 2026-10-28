"""
Spatial Network Fetcher & Conflict Zone Analyzer
=================================================
Uses OSMnx to fetch real-world street network geometry from OpenStreetMap
for the simulated intersections, and generates accurate pedestrian conflict zones.
"""

import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import os

# Configure OSMnx for cleaner execution
ox.settings.use_cache = True
ox.settings.log_console = False

class SpatialNetworkFetcher:
    def __init__(self):
        # Coordinates for our two Ahmedabad intersections
        self.intersections = {
            'INT_01_Signalized': {'lat': 23.0225, 'lon': 72.5714, 'name': 'CG_Road_Area'}, 
            'INT_02_Roundabout': {'lat': 23.0350, 'lon': 72.5650, 'name': 'Science_City_Area'}  
        }
        
        # Ahmedabad/Gujarat falls in UTM Zone 43N for accurate metric calculations
        self.local_crs = "EPSG:32643" 
        self.wgs84_crs = "EPSG:4326" # Standard for web maps
        
    def fetch_and_process_network(self):
        print("🌍 Fetching real-world street networks from OpenStreetMap...")
        
        all_edges = []
        all_conflict_zones = []
        
        for int_id, data in self.intersections.items():
            print(f"  Fetching network for {data['name']} ({data['lat']}, {data['lon']})...")
            
            try:
                # 1. Fetch the street network (300m radius)
                G = ox.graph_from_point((data['lat'], data['lon']), dist=300, network_type='drive')
                nodes, edges = ox.graph_to_gdfs(G)
                
                edges['intersection_id'] = int_id
                edges['intersection_name'] = data['name']
                all_edges.append(edges)
                
                # 2. Create an accurate 15-meter Pedestrian Conflict Zone
                center_point = Point(data['lon'], data['lat'])
                
                # Create a temporary GeoDataFrame to handle projections
                point_gdf = gpd.GeoDataFrame(
                    [{'intersection_id': int_id, 'intersection_name': data['name']}],
                    geometry=[center_point], 
                    crs=self.wgs84_crs
                )
                
                # Project to local metric CRS, buffer by exactly 15 meters, and project back
                point_projected = point_gdf.to_crs(self.local_crs)
                point_projected['geometry'] = point_projected.geometry.buffer(15)
                conflict_zone_final = point_projected.to_crs(self.wgs84_crs)
                conflict_zone_final['zone_type'] = 'Pedestrian_Vehicle_Conflict_Zone'
                
                all_conflict_zones.append(conflict_zone_final)
                
            except Exception as e:
                print(f"  ⚠️ Warning: Could not fetch network for {data['name']}. Error: {e}")
                
        # Combine all edges (they are already GeoDataFrames from OSMnx)
        self.edges_gdf = pd.concat(all_edges, ignore_index=True)
        
        # Combine all conflict zones
        self.conflict_zones_gdf = pd.concat(all_conflict_zones, ignore_index=True)
        
        print("✓ Successfully fetched and processed spatial networks.")
        return self.edges_gdf, self.conflict_zones_gdf

    def save_spatial_data(self):
        print(" Saving spatial data to GeoJSON format...")
        os.makedirs('data/processed', exist_ok=True)
        
        # Save edges (the actual roads)
        edges_path = 'data/processed/ahmedabad_road_network.geojson'
        self.edges_gdf.to_file(edges_path, driver='GeoJSON')
        print(f"  Saved road network to {edges_path}")
        
        # Save conflict zones
        zones_path = 'data/processed/pedestrian_conflict_zones.geojson'
        self.conflict_zones_gdf.to_file(zones_path, driver='GeoJSON')
        print(f"  Saved conflict zones to {zones_path}")

if __name__ == "__main__":
    fetcher = SpatialNetworkFetcher()
    edges, zones = fetcher.fetch_and_process_network()
    fetcher.save_spatial_data()
    
    print("\n" + "="*60)
    print("SPATIAL DATA SUMMARY")
    print("="*60)
    print(f"Total Road Segments (Edges) fetched: {len(edges)}")
    print(f"Total Pedestrian Conflict Zones generated: {len(zones)}")
    print("You can now join your tabular traffic data to these physical road segments!")