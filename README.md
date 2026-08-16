# Predictive Inventory & Workforce Planning System

An enterprise decision support system that forecasts future demand and converts those forecasts into actionable **inventory and workforce planning recommendations** using historical operational data.

## Overview

The system integrates demand forecasting, inventory planning, and workforce planning into a unified decision-support platform.

It uses historical operational data to forecast future demand and then evaluates inventory and workforce requirements over the planning horizon to identify potential shortages and recommend appropriate actions.

## Key Capabilities

* **Demand Forecasting** — Predicts future demand using a Prophet-based forecasting model.
* **Inventory Planning** — Determines replenishment requirements using forecasted demand, safety stock, reorder points, lead time, and inventory position.
* **Workforce Planning** — Identifies staffing gaps and recommends actions such as hiring, overtime, and hybrid workforce strategies.
* **Shortage Risk Detection** — Identifies potential inventory and workforce shortages before they occur.
* **Decision Support Dashboard** — Provides forecast, inventory, and workforce KPIs and planning insights through an interactive Streamlit dashboard.
* **90-Day Planning Horizon** — Supports integrated demand, inventory, and workforce planning over a 90-day forecast period.

## Objectives

* Forecast future demand
* Optimize inventory replenishment decisions
* Identify workforce requirements
* Detect inventory and workforce shortage risks
* Support proactive operational decision-making
* Provide an integrated view of business planning decisions

## Technology Stack

* **Python**
* **Pandas**
* **NumPy**
* **Scikit-learn**
* **XGBoost**
* **CatBoost**
* **Prophet**
* **Streamlit**
* **Plotly**

## Project Structure

The project is organized into modules for:

* Data processing and feature engineering
* Demand forecasting
* Inventory planning
* Workforce planning
* Decision-support metrics
* Interactive dashboard and visualizations

## Team

* **Mehul Khandelwal**
* **Shreyashi**

## Project Goal

The goal of the system is to move from **prediction to operational decision-making** by connecting demand forecasts with inventory replenishment and workforce planning.

**Forecast Demand → Inventory Planning → Workforce Planning → Business Decisions**
