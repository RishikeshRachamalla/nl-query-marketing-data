# Databricks notebook source
# Phase 1 — Bronze Ingestion Verification
# Run this in Databricks after uploading bronze_raw_transactions.csv via the UI

# COMMAND ----------
# Cell 1: Row and date range check
display(spark.sql("""
SELECT
    COUNT(*)                          AS total_rows,
    COUNT(DISTINCT invoice_no)        AS unique_invoices,
    COUNT(DISTINCT customer_id)       AS unique_customers,
    MIN(invoice_date)                 AS earliest_date,
    MAX(invoice_date)                 AS latest_date
FROM default.bronze_raw_transactions
"""))

# COMMAND ----------
# Cell 2: Data quality checks
display(spark.sql("""
SELECT
    SUM(CASE WHEN customer_id IS NULL           THEN 1 ELSE 0 END) AS null_customer_ids,
    SUM(CASE WHEN CAST(invoice_no AS STRING) LIKE 'C%' THEN 1 ELSE 0 END) AS cancellations,
    SUM(CASE WHEN quantity < 0                  THEN 1 ELSE 0 END) AS negative_qty_rows,
    SUM(CASE WHEN unit_price = 0               THEN 1 ELSE 0 END) AS zero_price_rows
FROM default.bronze_raw_transactions
"""))

# COMMAND ----------
# Cell 3: Top countries
display(spark.sql("""
SELECT country, COUNT(*) AS row_count
FROM default.bronze_raw_transactions
GROUP BY country
ORDER BY row_count DESC
LIMIT 10
"""))
