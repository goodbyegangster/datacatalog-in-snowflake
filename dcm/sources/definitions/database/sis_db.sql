-- noqa: disable=LT02

define database {{ sis_database_name }}
    data_retention_time_in_days = 0
    default_ddl_collation = 'utf8'
    OBJECT_VISIBILITY = $$
        organization_targets:
        - account: {{ snowflake_account_name }}
    $$
    comment = 'Streamlit in Snowflake 向けデータベース'
;
