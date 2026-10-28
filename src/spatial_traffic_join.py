"""
Spatial Traffic Join and Metric Calculation
============================================
Joins the tabular turning movement counts with the physical road network,
aggregates traffic volumes, and calculates a 'Congestion Index' for mapping.
"""

import pandas as pd
import geopandas as gpd
import os

class TrafficSpatialJoiner:
    def __init__(self):
        self.traffic_path = 'data/raw/ahmedabad_tmc_synthetic.csv'
        self.network_path = 'data/processed/ahmedabad_road_network.geojson'
        
    def load_data(self):
        print("Loading datasets...")
        # parse_dates ensures the timestamp is treated as actual time, not just text
        self.traffic_df = pd.read_csv(self.traffic_path, parse_dates=['timestamp'])
        self.network_gdf = gpd.read_file(self.network_path)
        print(f"  Loaded {len(self.traffic_df):,} traffic records and {len(self.network_gdf)} road segments.")

    def aggregate_traffic_metrics(self):
        print("Aggregating traffic metrics per intersection...")
        
        # 1. Calculate Total Daily Vehicle Volume per intersection
        total_volume = self.traffic_df.groupby('intersection_id')['vehicle_volume'].sum().reset_index()
        total_volume.rename(columns={'vehicle_volume': 'total_daily_volume'}, inplace=True)
        
        # 2. Calculate Peak Hour Volume
        self.traffic_df['hour'] = self.traffic_df['timestamp'].dt.hour
        hourly_volume = self.traffic_df.groupby(['intersection_id', 'hour'])['vehicle_volume'].sum().reset_index()
        hourly_volume.rename(columns={'vehicle_volume': 'hourly_volume'}, inplace=True)
        
        # Find the maximum hourly volume for each intersection
        peak_hour = hourly_volume.loc[hourly_volume.groupby('intersection_id')['hourly_volume'].idxmax()]
        peak_hour.rename(columns={'hourly_volume': 'peak_hour_volume', 'hour': 'peak_hour'}, inplace=True)
        
        # 3. Merge these metrics into a single summary table
        self.metrics_df = pd.merge(total_volume, peak_hour[['intersection_id', 'peak_hour_volume', 'peak_hour']], on='intersection_id')
        
        # 4. Calculate a 'Congestion Index' (0 to 100 scale) for visual mapping
        max_capacity = 3000 
        self.metrics_df['congestion_index'] = (self.metrics_df['peak_hour_volume'] / max_capacity) * 100
        self.metrics_df['congestion_index'] = self.metrics_df['congestion_index'].clip(upper=100)
        
        print("  Metrics aggregated successfully.")

    def perform_spatial_join(self):
        print("Joining metrics to physical road network...")
        
        # Merge the aggregated metrics onto the spatial road network
        self.enriched_gdf = pd.merge(self.network_gdf, self.metrics_df, on='intersection_id', how='left')
        
        # FIX: Only fill NaNs in the specific numeric columns we added.
        # This prevents Pandas from trying to put '0' into text columns like road names.
        numeric_cols = ['total_daily_volume', 'peak_hour_volume', 'peak_hour', 'congestion_index']
        for col in numeric_cols:
            if col in self.enriched_gdf.columns:
                self.enriched_gdf[col] = self.enriched_gdf[col].fillna(0)
                
        print(f"  Successfully enriched {len(self.enriched_gdf)} road segments with traffic data.")

    def save_enriched_data(self):
        print("Saving enriched spatial dataset...")
        output_path = 'data/processed/enriched_road_network.geojson'
        self.enriched_gdf.to_file(output_path, driver='GeoJSON')
        print(f"  Saved to {output_path}")

if __name__ == "__main__":
    joiner = TrafficSpatialJoiner()
    joiner.load_data()
    joiner.aggregate_traffic_metrics()
    joiner.perform_spatial_join()
    joiner.save_enriched_data()
    
    print("\n" + "="*60)
    print("ENRICHED DATA SUMMARY")
    print("="*60)
    
    # Safely print the results
    sig_vol = joiner.enriched_gdf[joiner.enriched_gdf['intersection_id'] == 'INT_01_Signalized']['peak_hour_volume'].iloc[0]
    round_vol = joiner.enriched_gdf[joiner.enriched_gdf['intersection_id'] == 'INT_02_Roundabout']['peak_hour_volume'].iloc[0]
    
    print(f"Total Road Segments Enriched: {len(joiner.enriched_gdf)}")
    print(f"Intersection 1 (Signalized) Peak Hour Volume: {sig_vol:,.0f} vehicles/hr")
    print(f"Intersection 2 (Roundabout) Peak Hour Volume: {round_vol:,.0f} vehicles/hr")
    print("Data is now ready for interactive map visualization!")