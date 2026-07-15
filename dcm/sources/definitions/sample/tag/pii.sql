-- noqa: disable=LT02

define tag {{ datacatalog_database_name }}.SAMPLE_TAG.PII
    allowed_values 'true', 'false'
    comment = '（サンプル）個人情報有無'
;
