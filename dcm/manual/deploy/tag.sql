-- noqa: disable=LT02

-- CAMPAIGN_LEADS テーブルに tag を付与
alter table <% sis_database_name %>.DATA_AD.CAMPAIGN_LEADS set tag
    <% sis_database_name %>.TAG.DATA_DOMAIN = 'marketing',
    <% sis_database_name %>.TAG.DATA_CATEGORY = 'transaction',
    <% sis_database_name %>.TAG.SENSITIVITY = 'restricted'
;

-- CAMPAIGN_LEADS テーブルの FULL_NAME 列に tag を付与
alter table <% sis_database_name %>.DATA_AD.CAMPAIGN_LEADS
    modify column FULL_NAME set tag
    <% sis_database_name %>.TAG.PII = 'true'
;

-- CAMPAIGN_LEADS テーブルの EMAIL 列に tag を付与
alter table <% sis_database_name %>.DATA_AD.CAMPAIGN_LEADS
    modify column EMAIL set tag
    <% sis_database_name %>.TAG.PII = 'true'
;

-- PRODUCTS テーブルに tag を付与
alter table <% sis_database_name %>.DATA_SALES.PRODUCTS set tag
    <% sis_database_name %>.TAG.DATA_DOMAIN = 'sales',
    <% sis_database_name %>.TAG.DATA_CATEGORY = 'master',
    <% sis_database_name %>.TAG.SENSITIVITY = 'internal'
;

-- PRODUCT_CATEGORIES テーブルに tag を付与
alter table <% sis_database_name %>.DATA_SALES.PRODUCT_CATEGORIES set tag
    <% sis_database_name %>.TAG.DATA_DOMAIN = 'sales',
    <% sis_database_name %>.TAG.DATA_CATEGORY = 'master',
    <% sis_database_name %>.TAG.SENSITIVITY = 'internal'
;
