-- noqa: disable=LT02

define tag {{ sis_database_name }}.TAG.SENSITIVITY
    allowed_values 'public', 'internal', 'confidential', 'restricted'
    comment = '（サンプル）データ機密度'
;
