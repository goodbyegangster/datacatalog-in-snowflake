-- view 作成
-- tag が付与された view を dcm では管理できないため、手動で作成を行っている
create view if not exists <% datacatalog_database_name %>.SAMPLE_DATA_SALES.V_PRODUCTS (
    PRODUCT_ID comment '商品ID',
    PRODUCT_NAME comment '商品名',
    CATEGORY_ID comment '商品カテゴリID',
    PRICE comment '価格',
    CREATED_AT comment 'レコード作成日時'
)
comment = '（サンプル）商品マスター（日用品）'
as
select *
from <% datacatalog_database_name %>.SAMPLE_DATA_SALES.PRODUCTS
where
    CATEGORY_ID = 1
;

-- V_PRODUCTS ビューに tag を付与
alter view <% datacatalog_database_name %>.SAMPLE_DATA_SALES.V_PRODUCTS set tag
    <% datacatalog_database_name %>.SAMPLE_TAG.DATA_DOMAIN = 'sales',
    <% datacatalog_database_name %>.SAMPLE_TAG.DATA_CATEGORY = 'master',
    <% datacatalog_database_name %>.SAMPLE_TAG.SENSITIVITY = 'internal'
;
