"""
Spatial Network Fetcher & Conflict Zone Analyzer
=================================================
Uses OSMnx to fetch real-world street network geometry from OpenStreetMap
for the simulated intersections, and generates pedestrian conflict zones.
"""

import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point, Polygon
import pandas as pd
import os

class SpatialNetworkFetcher:
    def __init__(self):
        # Coordinates for our two Ahmedabad intersections
        self.intersections = {
            'INT_01_Signalized': {'lat': 23.0225, 'lon': 72.5714, 'name': 'CG_Road_Area'}, # Near CG Road
            'INT_02_Roundabout': {'lat': 23.0350, 'lon': 72.5650, 'name': 'Science_City_Area'}  # Near Science City
        }
        
    def fetch_and_process_network(self):
        print("🌍 Fetching real-world street networks from OpenStreetMap...")
        
        all_edges = []
        all_conflict_zones = []
        
        for int_id, data in self.intersections.items():
            print(f"  Fetching network for {data['name']} ({data['lat']}, {data['lon']})...")
            
            # 1. Fetch the street network (300m radius around the point)
            # network_type='drive' ensures we get motorable roads, excluding footpaths for this specific vehicle analysis
            G = ox.graph_from_point((data['lat'], data['lon']), dist=300, network_type='drive')
            
            # 2. Convert the graph to GeoDataFrames (Nodes and Edges)
            nodes, edges = ox.graph_to_gdfs(G)
            
            # Add intersection ID to the edges so we can join our traffic data to them later
            edges['intersection_id'] = int_id
            edges['intersection_name'] = data['name']
            all_edges.append(edges)
            
            # 3. Create a "Pedestrian Conflict Zone" (15-meter buffer around the center point)
            # This represents the area where right-turning vehicles conflict with pedestrians
            center_point = Point(data['lon'], data['lat'])
            conflict_zone = center_point.buffer(0.00015) # ~15 meters in decimal degrees
            
            all_conflict_zones.append({
                'intersection_id': int_id,
                'intersection_name': data['name'],
                'geometry': conflict_zone,
                'zone_type': 'Pedestrian_Vehicle_Conflict_Zone'
            })
            
        # Combine all edges into one GeoDataFrame
        self.edges_gdf = gpd.pd.concat(all_edges, ignore_index=True)
        self.edges_gdf = gpd.GeoDataFrame(self.edges_gdf, geometry='geometry', crs="EPSG:4326")
        
        # Combine all conflict zones into one GeoDataFrame
        self.conflict_zones_gdf = gpd.GeoDataFrame(
            all_conflict_zones, 
            geometry='geometry', 
            crs="EPSG:4326"
        )
        
        print("✓ Successfully fetched and processed spatial networks.")
        return self.edges_gdf, self.conflict_zones_gdf

    def save_spatial_data(self):
        print("💾 Saving spatial data to GeoJSON format...")
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