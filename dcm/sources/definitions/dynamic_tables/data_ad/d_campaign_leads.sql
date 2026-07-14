define dynamic table {{ sis_database_name }}.DATA_AD.D_CAMPAIGN_LEADS (
    LEAD_ID number comment 'リードID',
    CAMPAIGN_NAME varchar(255) comment '流入元キャンペーン名'
)
target_lag = downstream
warehouse = {{ sis_warehouse_name }}
comment = '（サンプル）リード情報'
as
    select
        LEAD_ID,
        CAMPAIGN_NAME
    from {{ sis_database_name }}.DATA_AD.CAMPAIGN_LEADS
;
