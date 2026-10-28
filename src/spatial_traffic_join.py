"""
Scenario-Based Spatial Traffic Join
====================================
Calculates congestion metrics for three critical times of day:
Morning Peak (09:00), Midday Off-Peak (14:00), and Evening Peak (19:00).
"""

import pandas as pd
import geopandas as gpd
import os

class ScenarioTrafficJoiner:
    def __init__(self):
        self.traffic_path = 'data/raw/ahmedabad_tmc_synthetic.csv'
        self.network_path = 'data/processed/ahmedabad_road_network.geojson'
        self.zones_path = 'data/processed/pedestrian_conflict_zones.geojson'
        
    def load_data(self):
        print("Loading datasets...")
        self.traffic_df = pd.read_csv(self.traffic_path, parse_dates=['timestamp'])
        self.network_gdf = gpd.read_file(self.network_path)
        self.zones_gdf = gpd.read_file(self.zones_path)
        print(f"  Loaded {len(self.traffic_df):,} records and {len(self.network_gdf)} segments.")

    def calculate_scenario_metrics(self):
        print("Calculating metrics for Morning (09:00), Midday (14:00), and Evening (19:00)...")
        
        self.traffic_df['hour'] = self.traffic_df['timestamp'].dt.hour
        
        # Filter for our 3 specific hours
        target_hours = [9, 14, 19]
        filtered_traffic = self.traffic_df[self.traffic_df['hour'].isin(target_hours)]
        
        # Calculate average volume for each hour per intersection
        hourly_avg = filtered_traffic.groupby(['intersection_id', 'hour'])['vehicle_volume'].mean().reset_index()
        hourly_avg = hourly_avg.rename(columns={'vehicle_volume': 'avg_hourly_volume'})
        
        # Calculate Congestion Index for each hour
        capacity_per_approach = 1800.0
        approaches = 4.0
        
        def calc_index(row):
            per_approach = float(row['avg_hourly_volume']) / approaches
            idx = (per_approach / capacity_per_approach) * 100.0
            return round(min(idx, 100.0), 1)
            
        hourly_avg['congestion_index'] = hourly_avg.apply(calc_index, axis=1)
        
        # Pivot the table so each hour is a column
        self.scenario_metrics = hourly_avg.pivot_table(
            index='intersection_id', 
            columns='hour', 
            values=['avg_hourly_volume', 'congestion_index']
        ).reset_index()
        
        # Flatten the multi-index columns
        self.scenario_metrics.columns = [f"{col[0]}_{col[1]}" if col[1] != '' else col[0] for col in self.scenario_metrics.columns]
        # Rename for clarity
        self.scenario_metrics = self.scenario_metrics.rename(columns={
            'intersection_id': 'intersection_id',
            'avg_hourly_volume_9': 'vol_09', 'congestion_index_9': 'idx_09',
            'avg_hourly_volume_14': 'vol_14', 'congestion_index_14': 'idx_14',
            'avg_hourly_volume_19': 'vol_19', 'congestion_index_19': 'idx_19'
        })
        
        print("  Scenario metrics calculated successfully.")

    def save_enriched_network(self):
        print("Merging metrics with road network...")
        
        # Merge metrics onto the network
        enriched = pd.merge(self.network_gdf, self.scenario_metrics, on='intersection_id', how='left')
        
        # Fill NaNs with 0
        numeric_cols = ['vol_09', 'idx_09', 'vol_14', 'idx_14', 'vol_19', 'idx_19']
        for col in numeric_cols:
            enriched[col] = enriched[col].fillna(0)
            
        # Save to GeoJSON
        enriched.to_file('data/processed/scenario_road_network.geojson', driver='GeoJSON')
        print("  Enriched network saved.")

if __name__ == "__main__":
    joiner = ScenarioTrafficJoiner()
    joiner.load_data()
    joiner.calculate_scenario_metrics()
    joiner.save_enriched_network()
    print("\n✅ Data prep complete. Ready for map building!")