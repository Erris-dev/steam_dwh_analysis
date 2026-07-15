# 📏 Naming Conventions

This document outlines the naming conventions used throughout the **Steam Data Warehouse** project. Following these standards ensures consistency, readability, maintainability, and clear data lineage across the Medallion Architecture.

---

## 📑 Table of Contents

1. [General Principles](#general-principles)
2. [Schema Naming](#schema-naming)
3. [Table Naming Conventions](#table-naming-conventions)

   * [Bronze Rules](#bronze-rules)
   * [Silver Rules](#silver-rules)
   * [Gold Rules](#gold-rules)
4. [Column Naming Conventions](#column-naming-conventions)

   * [Primary & Surrogate Keys](#primary--surrogate-keys)
   * [Foreign Keys](#foreign-keys)
   * [Technical Columns](#technical-columns)
5. [Views](#views)
6. [Stored Procedures / ETL Jobs](#stored-procedures--etl-jobs)

---

# 📝 General Principles

* **Case Style:** Use `snake_case` (lowercase with underscores).
* **Language:** All database objects must use **English**.
* **Naming:** Prefer descriptive names over abbreviations unless they are widely recognized (e.g., `api`, `id`).
* **Reserved Words:** Avoid SQL reserved keywords.
* **Pluralization:** Tables should use plural nouns where appropriate (e.g., `games`, `developers`, `publishers`).
* **Consistency:** Apply naming conventions consistently across every Medallion layer.

---

# 🗂️ Schema Naming

The project follows the Medallion Architecture using dedicated PostgreSQL schemas.

| Schema   | Purpose                       |
| :------- | :---------------------------- |
| `bronze` | Raw ingested API data         |
| `silver` | Cleaned and standardized data |
| `gold`   | Star schema for analytics     |

---

# 🏗️ Table Naming Conventions

## Bronze Rules

The Bronze layer stores raw API responses exactly as they are received from the source.

* **Pattern:** `<source>_<entity>_raw`
* **`<source>`:** Data source identifier (`steam`, `steamspy`, etc.)
* **`<entity>`:** Resource retrieved from the API.

### Examples

```text
steam_games_raw
steam_reviews_raw
steam_publishers_raw
steam_developers_raw
```

---

## Silver Rules

The Silver layer stores validated, cleaned, and normalized data.

* **Pattern:** `<entity>`
* Tables represent business entities rather than API endpoints.
* Nested API objects should be split into relational tables.

### Examples

```text
games
developers
publishers
genres
game_genres
reviews
```

---

## Gold Rules

The Gold layer contains business-oriented analytical models using a dimensional star schema.

* **Dimension Pattern:** `dim_<entity>`
* **Fact Pattern:** `fact_<entity>`
* **Report View Pattern:** `report_<business_area>`

### Examples

```text
dim_game
dim_developer
dim_publisher
dim_genre
dim_date

fact_game_metrics

report_top_publishers
report_genre_performance
```

---

### Glossary

| Pattern   | Meaning         | Example               |
| :-------- | :-------------- | :-------------------- |
| `dim_`    | Dimension table | `dim_game`            |
| `fact_`   | Fact table      | `fact_game_metrics`   |
| `report_` | Reporting view  | `report_genre_trends` |

---

# 🔑 Column Naming Conventions

## Primary & Surrogate Keys

Every dimension table uses a surrogate key as its primary key.

* **Pattern:** `<entity>_key`

### Examples

```text
game_key
developer_key
publisher_key
genre_key
date_key
```

---

## Foreign Keys

Fact tables reference dimension surrogate keys.

* **Pattern:** `<entity>_key`

### Examples

```text
game_key
developer_key
publisher_key
genre_key
date_key
```

---

## Business Keys

Identifiers originating from the Steam API should retain their original meaning.

* **Pattern:** `<entity>_id`

### Examples

```text
game_id
developer_id
publisher_id
review_id
```

---

## Technical Columns

System-generated metadata used for auditing and ETL tracking.

* **Pattern:** `dwh_<column_name>`

### Examples

```text
dwh_load_timestamp
dwh_source
dwh_batch_id
dwh_last_updated
```

---

# 👁️ Views

Views intended for reporting should clearly describe their purpose.

* **Pattern:** `report_<business_area>`

### Examples

```text
report_top_games
report_price_trends
report_genre_popularity
report_review_summary
```

---

# ⚙️ Stored Procedures / ETL Jobs

Database procedures or ETL jobs should indicate the Medallion layer they populate.

* **Pattern:** `load_<layer>`

### Examples

```text
load_bronze
load_silver
load_gold
```

For transformation-specific jobs, use descriptive names.

```text
transform_games
build_dimensions
build_fact_game_metrics
validate_silver_data
refresh_gold_layer
```
