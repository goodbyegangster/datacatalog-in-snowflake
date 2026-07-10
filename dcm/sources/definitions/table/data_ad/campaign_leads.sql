-- noqa: disable=LT02

define table {{ sis_database_name }}.DATA_AD.CAMPAIGN_LEADS (
    LEAD_ID number comment 'リードID',
    FULL_NAME varchar(255) not null comment '氏名',
    EMAIL varchar(255) comment 'メールアドレス',
    CAMPAIGN_NAME varchar(255) comment '流入元キャンペーン名',
    CREATED_AT timestamp_ntz not null comment 'リード作成日時',
    constraint pk_01 primary key (LEAD_ID) not enforced
)
comment = 'マーケティングキャンペーンで獲得したリード情報'
;
