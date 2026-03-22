# Databricks notebook source
# Phase 2 — Silver Layer Transformation (placeholder)
# Will clean bronze, join enrichment, compute RFM scores

# COMMAND ----------
# Verify enrichment table after upload
display(spark.sql("""
SELECT
    COUNT(*)                      AS total_customers,
    COUNT(DISTINCT loyalty_tier)  AS tiers,
    COUNT(DISTINCT signup_channel)AS channels
FROM default.silver_enriched_customers
"""))

# COMMAND ----------
# Loyalty tier distribution
display(spark.sql("""
SELECT
    loyalty_tier,
    COUNT(*)                              AS customer_count,
    ROUND(AVG(total_transactions), 1)     AS avg_txns,
    ROUND(AVG(loyalty_points), 0)         AS avg_points
FROM default.silver_enriched_customers
GROUP BY loyalty_tier
ORDER BY customer_count DESC
"""))

# COMMAND ----------
# Signup channel distribution
display(spark.sql("""
SELECT
    signup_channel,
    COUNT(*)                                          AS customers,
    ROUND(AVG(CAST(email_opt_in AS INT)) * 100, 1)   AS email_optin_pct,
    ROUND(AVG(CAST(campaign_responder AS INT)) * 100, 1) AS campaign_resp_pct
FROM default.silver_enriched_customers
GROUP BY signup_channel
ORDER BY customers DESC
"""))
