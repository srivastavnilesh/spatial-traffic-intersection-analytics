# Ahmedabad Smart City: Spatial Traffic Analytics and Intersection Digital Twin

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![GeoPandas](https://img.shields.io/badge/GeoPandas-Spatial-3F4F75?logo=python)
![Folium](https://img.shields.io/badge/Folium-Interactive_Maps-77B829)
![OSMnx](https://img.shields.io/badge/OSMnx-Street_Networks-orange)

## Project Overview

An end-to-end spatial data engineering pipeline that converts raw turning movement counts into a suite of four interactive geospatial dashboards for urban intersection analysis. The pipeline is calibrated for Ahmedabad, Gujarat and covers two real junction types: a 4-leg signalized intersection (CG Road area) and a 3-leg roundabout (Science City area).

The goal was simple: intersection analysis in India still ends as static PDFs and Excel sheets. This project treats an intersection as a live, queryable data product.

## The Dashboard Suite

Four complementary dashboards, each answering a different question for a different stakeholder.

### 1. Network Congestion Hotspot Map
File: `outputs/ahmedabad_traffic_dashboard.html`
- Question answered: Where does congestion form on the real street network?
- How it was built: OSMnx street network joined to traffic metrics using a distance-aware 50-meter bottleneck radius, with 15-meter UTM-projected pedestrian conflict buffers overlaid.
- What it helps with: City-level screening. Planners can instantly see which corridors bottleneck and exactly where pedestrians conflict with turning vehicles.

### 2. 24-Hour Dynamic Time-Series Map (Experimental Prototype)
File: `outputs/dynamic_traffic_dashboard.html`
- Question answered: How does congestion build and dissipate across the day?
- How it was built: Hourly congestion indices serialized into a time-indexed style dictionary and rendered with Folium's TimeSliderChoropleth.
- What it helps with: Communicating diurnal traffic behavior to non-technical audiences.
- Honest note: Folium's time-slider has known rendering limitations with line geometries, which motivated the scenario dashboard below.

### 3. Scenario Comparison Dashboard
File: `outputs/scenario_traffic_dashboard.html`
- Question answered: Which time-of-day scenario is worst, and exactly where?
- How it was built: Three toggleable layer groups (Morning Peak 09:00, Midday 14:00, Evening Peak 19:00) over the OSMnx network, each segment carrying a rich HTML popup with volume, congestion index, and Level of Service.
- What it helps with: Stakeholder decision meetings. Compare peak scenarios side by side without needing a live data feed.

### 4. Intersection Digital Twin (Flagship Deliverable)
File: `outputs/intersection_digital_twin.html`
- Question answered: What are the engineering design parameters for each approach leg?
- How it was built: Approach-level geometric model combined with Highway Capacity Manual style metrics: Level of Service (A to F), Volume-to-Capacity ratio, Peak Hour Factor, and Turning Movement Counts per approach.
- What it helps with: Real design decisions. In the synthetic run, Eastbound approaches operate at LOS F (V/C 1.11) during peak hour while Westbound flows freely at LOS A (V/C 0.39). That single finding justifies a dedicated turn lane or signal retiming.

## How the Four Fit Together

The suite is a funnel:
1. Hotspot map: spatial screening (where).
2. Time-series map: temporal behavior (when, continuous).
3. Scenario dashboard: discrete scenario comparison (when, decision-ready).
4. Digital twin: engineering design parameters (why, and how to fix it).

## Pipeline Architecture

1. Synthetic TMC generation (`src/synthetic_traffic_generator.py`): 7 days of hourly turning movement counts across vehicle classes (2W, 3W, 4W, HMV) plus pedestrian volumes, with Ahmedabad-specific morning and evening peak profiles and night-time heavy vehicle patterns.
2. Real-world geometry fetch (`src/spatial_network_fetcher.py`): OSMnx street network download plus UTM-projected (EPSG:32643) 15-meter pedestrian conflict buffers.
3. Spatial join and metrics (`src/spatial_traffic_join.py`, `src/traffic_engineering_engine.py`): distance-aware joins, hourly aggregation, and LOS, V/C, and PHF calculations per approach leg.
4. Visualization layer (`src/interactive_map_builder.py`, `src/digital_twin_map_builder.py`): Folium dashboards with layer control, interactive popups, legends, and fullscreen presentation mode.

## Tech Stack

- Data processing: pandas, numpy
- Spatial engineering: geopandas, osmnx, shapely
- Visualization: folium
- Workflow: Git, GitHub, virtual environments

## How to Run

1. Clone and enter the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/spatial-traffic-intersection-analytics.git
   cd spatial-traffic-intersection-analytics