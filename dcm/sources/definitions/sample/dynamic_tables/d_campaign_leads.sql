define dynamic table {{ datacatalog_database_name }}.SAMPLE_DATA_AD.D_CAMPAIGN_LEADS (
    LEAD_ID number comment 'リードID',
    CAMPAIGN_NAME varchar(255) comment '流入元キャンペーン名'
)
target_lag = downstream
warehouse = {{ datacatalog_warehouse_name }}
comment = '（サンプル）リード情報'
as
    select
        LEAD_ID,
        CAMPAIGN_NAME
    from {{ datacatalog_database_name }}.SAMPLE_DATA_AD.CAMPAIGN_LEADS
;
