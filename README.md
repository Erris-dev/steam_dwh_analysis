# Steam Data Warehouse

This project demonstrates a comprehensive data engineering and analytics solution, from ingesting data from the Steam API to building a modern data warehouse using the Medallion Architecture. Raw data is stored in the Bronze layer, cleaned and standardized in the Silver layer, and transformed into a star schema in the Gold layer for efficient analytics. Designed as a portfolio project, it showcases industry best practices in ETL pipelines, dimensional data modeling, data quality, and business intelligence through SQL analysis and interactive dashboards.

---

## Project Requirements

### Building the Data Warehouse (Data Engineering)

#### Objective

Develop a modern data warehouse using PostgreSQL and the Medallion Architecture to consolidate Steam data into an analytics-ready data model for reporting and business intelligence.

#### Specifications

* **Data Sources**: Extract data from the Steam API (and additional public Steam data sources where applicable).
* **Data Ingestion**: Store raw API responses in the Bronze layer while preserving the original data.
* **Data Quality**: Clean, validate, and standardize data in the Silver layer by handling missing values, duplicates, inconsistent formats, and nested JSON structures.
* **Data Modeling**: Transform curated data into a dimensional star schema in the Gold layer consisting of fact and dimension tables optimized for analytical queries.
* **Scope**: Process the latest available data from the APIs; historical versioning is not required.
* **Documentation**: Provide comprehensive documentation of the ETL pipeline, database schema, and dimensional model.

---

### BI: Analytics & Reporting (Data Analysis)

#### Objective

Develop SQL-based analytics and interactive dashboards to deliver insights into:

* **Game Performance**
* **Genre Trends**
* **Publisher & Developer Performance**
* **Review & Rating Analysis**
* **Pricing Trends**
* **Release Trends**

These insights provide meaningful business metrics that support data-driven decision-making and demonstrate analytical capabilities.

---

## 🏗️ Architecture

This project follows the Medallion Architecture:

* **Bronze Layer** → Raw data ingestion from the Steam API.
* **Silver Layer** → Data cleansing, validation, normalization, and transformation.
* **Gold Layer** → Dimensional star schema consisting of fact and dimension tables for analytics and reporting.
* **Analytics Layer** → SQL queries and Power BI dashboards built on top of the Gold layer.
