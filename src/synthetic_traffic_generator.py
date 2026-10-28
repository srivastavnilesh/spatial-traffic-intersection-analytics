"""
Synthetic Spatial Traffic Data Generator (Ahmedabad)
=====================================================
Generates realistic hourly turning movement counts (TMC) and pedestrian volumes 
for a 4-legged signalized intersection and a 3-legged roundabout in Ahmedabad.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

class SyntheticTrafficGenerator:
    def __init__(self, days_to_simulate=7):
        self.days = days_to_simulate
        # Coordinates for two hypothetical intersections in Ahmedabad
        self.intersections = {
            'INT_01_Signalized': {'lat': 23.0225, 'lon': 72.5714, 'type': '4-Leg Signalized'}, # Near CG Road
            'INT_02_Roundabout': {'lat': 23.0350, 'lon': 72.5650, 'type': '3-Leg Roundabout'}  # Near Science City
        }
        np.random.seed(42)

    def _get_peak_hour_multiplier(self, hour):
        """Simulates Ahmedabad's distinct morning and evening traffic peaks."""
        if 8 <= hour <= 11:  # Morning Peak
            return np.random.uniform(1.8, 2.5)
        elif 17 <= hour <= 20:  # Evening Peak
            return np.random.uniform(2.0, 2.8)
        elif 22 <= hour or hour <= 5:  # Night (Low traffic)
            return np.random.uniform(0.1, 0.3)
        else:  # Off-peak daytime
            return np.random.uniform(0.8, 1.2)

    def _get_hmv_multiplier(self, hour):
        """Heavy vehicles usually avoid peak hours in Indian cities due to restrictions."""
        if 9 <= hour <= 21:
            return np.random.uniform(0.1, 0.3) # Low HMV during day
        else:
            return np.random.uniform(1.5, 2.5) # High HMV at night

    def generate_turning_movements(self):
        print(f"🚦 Generating {self.days} days of Turning Movement Counts (TMC)...")
        
        all_data = []
        start_date = datetime(2026, 10, 1) # Simulating recent data
        
        for day in range(self.days):
            current_date = start_date + timedelta(days=day)
            is_weekend = current_date.weekday() >= 5
            
            for int_id, int_data in self.intersections.items():
                # Define approach legs based on intersection type
                legs = ['North', 'East', 'South', 'West'] if '4-Leg' in int_data['type'] else ['North', 'East', 'South']
                movements = ['Left', 'Through', 'Right']
                vehicle_classes = ['2W', '3W_Auto', '4W_Car', 'HMV_Bus_Truck']
                
                for hour in range(24):
                    for leg in legs:
                        for movement in movements:
                            for v_class in vehicle_classes:
                                # Base volume
                                base_vol = 10 
                                if v_class == '2W': base_vol = 40
                                elif v_class == '3W_Auto': base_vol = 25
                                elif v_class == '4W_Car': base_vol = 20
                                elif v_class == 'HMV_Bus_Truck': base_vol = 5
                                
                                # Apply multipliers
                                peak_mult = self._get_peak_hour_multiplier(hour)
                                hmv_mult = self._get_hmv_multiplier(hour) if v_class == 'HMV_Bus_Truck' else 1.0
                                weekend_mult = 0.6 if is_weekend else 1.0
                                
                                # Calculate final volume
                                volume = int(base_vol * peak_mult * hmv_mult * weekend_mult * np.random.uniform(0.8, 1.2))
                                
                                # Generate Pedestrian Volume (only for Through and Left movements at crosswalks)
                                ped_vol = 0
                                if movement in ['Through', 'Left'] and v_class == '4W_Car':
                                    ped_vol = int(volume * np.random.uniform(0.1, 0.4) * peak_mult)
                                
                                all_data.append({
                                    'timestamp': current_date.replace(hour=hour),
                                    'intersection_id': int_id,
                                    'intersection_type': int_data['type'],
                                    'latitude': int_data['lat'],
                                    'longitude': int_data['lon'],
                                    'approach_leg': leg,
                                    'movement_type': movement,
                                    'vehicle_class': v_class,
                                    'vehicle_volume': volume,
                                    'pedestrian_volume': ped_vol
                                })
                                
        df = pd.DataFrame(all_data)
        print(f"✓ Generated {len(df):,} turning movement records.")
        return df

    def save_to_csv(self, df, output_path='data/raw/ahmedabad_tmc_synthetic.csv'):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f" Saved dataset to {output_path}")

if __name__ == "__main__":
    generator = SyntheticTrafficGenerator(days_to_simulate=7)
    df = generator.generate_turning_movements()
    generator.save_to_csv(df)
    
    print("\n" + "="*60)
    print("DATA SUMMARY")
    print("="*60)
    print(f"Total Records: {len(df):,}")
    print(f"Intersections: {df['intersection_id'].nunique()}")
    print(f"Peak Hour (Max Volume): {df.groupby(df['timestamp'].dt.hour)['vehicle_volume'].sum().idxmax()}:00 hrs")
    print(f"Total HMV Volume: {df[df['vehicle_class'] == 'HMV_Bus_Truck']['vehicle_volume'].sum():,}")
    print(f"Total Pedestrian Volume: {df['pedestrian_volume'].sum():,}")