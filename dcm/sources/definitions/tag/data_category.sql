-- noqa: disable=LT02

define tag {{ datacatalog_database_name }}.TAG.DATA_CATEGORY
    allowed_values 'master', 'transaction', 'reference', 'metadata'
    comment = '（サンプル）データ種別'
;
