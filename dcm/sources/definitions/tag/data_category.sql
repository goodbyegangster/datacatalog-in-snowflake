-- noqa: disable=LT02

define tag {{ sis_database_name }}.TAG.DATA_CATEGORY
    allowed_values 'master', 'transaction', 'reference', 'metadata'
    comment = 'データ種別'
;
