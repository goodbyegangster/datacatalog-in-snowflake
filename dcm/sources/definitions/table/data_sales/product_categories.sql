-- noqa: disable=LT02

define table {{ sis_database_name }}.DATA_SALES.PRODUCT_CATEGORIES (
    CATEGORY_ID number comment 'カテゴリID',
    CATEGORY_NAME varchar(100) not null comment 'カテゴリ名',
    DESCRIPTION varchar(255) comment '説明',
    CREATED_AT timestamp_ntz not null comment 'レコード作成日時',
    constraint pk_01 primary key (CATEGORY_ID) not enforced
)
comment = '（サンプル）商品カテゴリマスター'
;
