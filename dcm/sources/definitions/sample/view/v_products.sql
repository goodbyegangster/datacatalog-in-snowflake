-- noqa: disable=LT02

define view {{ datacatalog_database_name }}.SAMPLE_DATA_SALES.V_PRODUCTS (
    PRODUCT_ID comment '商品ID',
    PRODUCT_NAME comment '商品名',
    CATEGORY_ID comment '商品カテゴリID',
    PRICE  comment '価格',
    CREATED_AT comment 'レコード作成日時'
)
comment = '（サンプル）商品マスター（日用品）'
as
select *
from {{ datacatalog_database_name }}.SAMPLE_DATA_SALES.PRODUCTS
where
    CATEGORY_ID = 1
;
