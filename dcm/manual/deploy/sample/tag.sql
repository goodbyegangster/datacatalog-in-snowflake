-- CAMPAIGN_LEADS テーブルに tag を付与
alter table <% datacatalog_database_name %>.SAMPLE_DATA_AD.CAMPAIGN_LEADS set tag
    <% datacatalog_database_name %>.SAMPLE_TAG.DATA_DOMAIN = 'marketing',
    <% datacatalog_database_name %>.SAMPLE_TAG.DATA_CATEGORY = 'transaction',
    <% datacatalog_database_name %>.SAMPLE_TAG.SENSITIVITY = 'restricted'
;

-- CAMPAIGN_LEADS テーブルの FULL_NAME 列に tag を付与
alter table <% datacatalog_database_name %>.SAMPLE_DATA_AD.CAMPAIGN_LEADS modify column FULL_NAME set tag
    <% datacatalog_database_name %>.SAMPLE_TAG.PII = 'true'
;

-- CAMPAIGN_LEADS テーブルの EMAIL 列に tag を付与
alter table <% datacatalog_database_name %>.SAMPLE_DATA_AD.CAMPAIGN_LEADS modify column EMAIL set tag
    <% datacatalog_database_name %>.SAMPLE_TAG.PII = 'true'
;

-- D_CAMPAIGN_LEADS テーブルに tag を付与
alter table <% datacatalog_database_name %>.SAMPLE_DATA_AD.D_CAMPAIGN_LEADS set tag
    <% datacatalog_database_name %>.SAMPLE_TAG.DATA_DOMAIN = 'marketing',
    <% datacatalog_database_name %>.SAMPLE_TAG.DATA_CATEGORY = 'transaction',
    <% datacatalog_database_name %>.SAMPLE_TAG.SENSITIVITY = 'internal'
;

-- PRODUCTS テーブルに tag を付与
alter table <% datacatalog_database_name %>.SAMPLE_DATA_SALES.PRODUCTS set tag
    <% datacatalog_database_name %>.SAMPLE_TAG.DATA_DOMAIN = 'sales',
    <% datacatalog_database_name %>.SAMPLE_TAG.DATA_CATEGORY = 'master',
    <% datacatalog_database_name %>.SAMPLE_TAG.SENSITIVITY = 'internal'
;

-- PRODUCT_CATEGORIES テーブルに tag を付与
alter table <% datacatalog_database_name %>.SAMPLE_DATA_SALES.PRODUCT_CATEGORIES set tag
    <% datacatalog_database_name %>.SAMPLE_TAG.DATA_DOMAIN = 'sales',
    <% datacatalog_database_name %>.SAMPLE_TAG.DATA_CATEGORY = 'master',
    <% datacatalog_database_name %>.SAMPLE_TAG.SENSITIVITY = 'internal'
;

-- V_PRODUCTS ビューに tag を付与
alter view <% datacatalog_database_name %>.SAMPLE_DATA_SALES.V_PRODUCTS set tag
    <% datacatalog_database_name %>.SAMPLE_TAG.DATA_DOMAIN = 'sales',
    <% datacatalog_database_name %>.SAMPLE_TAG.DATA_CATEGORY = 'master',
    <% datacatalog_database_name %>.SAMPLE_TAG.SENSITIVITY = 'internal'
;
