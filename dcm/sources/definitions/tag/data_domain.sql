-- noqa: disable=LT02

define tag {{ sis_database_name }}.TAG.DATA_DOMAIN
    allowed_values 'sales', 'marketing', 'finance', 'product', 'corporate'
    comment = 'データドメイン'
;
