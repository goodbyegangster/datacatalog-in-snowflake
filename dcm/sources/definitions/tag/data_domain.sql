-- noqa: disable=LT02

define tag {{ datacatalog_database_name }}.TAG.DATA_DOMAIN
    allowed_values 'sales', 'marketing', 'finance', 'product', 'corporate'
    comment = '（サンプル）データドメイン'
;
