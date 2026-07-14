-- noqa: disable=LT02

define table {{ datacatalog_database_name }}.DATA_SALES.PRODUCTS (
    PRODUCT_ID number comment '商品ID',
    PRODUCT_NAME varchar(255) not null comment '商品名',
    CATEGORY_ID number comment '商品カテゴリID',
    PRICE number(10, 2) comment '価格',
    CREATED_AT timestamp_ntz not null comment 'レコード作成日時',
    constraint pk_01 primary key (PRODUCT_ID) not enforced,
    constraint fk_01 foreign key (CATEGORY_ID)
        references {{ datacatalog_database_name }}.DATA_SALES.PRODUCT_CATEGORIES (CATEGORY_ID)
        not enforced
)
comment = '（サンプル）商品マスター'
;
