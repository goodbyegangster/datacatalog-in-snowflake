-- noqa: disable=LT02

define tag {{ datacatalog_database_name }}.SAMPLE_TAG.SENSITIVITY
    allowed_values 'public', 'internal', 'confidential', 'restricted'
    comment = '（サンプル）データ機密度'
;
