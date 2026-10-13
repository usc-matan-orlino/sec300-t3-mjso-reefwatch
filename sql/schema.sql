-- ReefWatch: Azure SQL schema
-- Stores one summary row per day.

CREATE TABLE daily_summary (
    summary_date          DATE           NOT NULL PRIMARY KEY,  -- PK prevents duplicate summaries
    total_surveys         INT            NOT NULL,
    total_survey_cost     DECIMAL(10, 2) NOT NULL,
    top_species           NVARCHAR(100)  NULL,                  -- most frequently observed species
    low_equipment_alerts  NVARCHAR(500)  NULL,                  -- comma-separated equipment names
    created_at            DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME()
);
