-- noqa: disable=LT02

define tag {{ datacatalog_database_name }}.TAG.SENSITIVITY
    allowed_values 'public', 'internal', 'confidential', 'restricted'
    comment = '（サンプル）データ機密度'
;
