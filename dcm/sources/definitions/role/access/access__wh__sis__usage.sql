-- noqa: disable=LT02

define role {{ sis_role_name_prefix }}_ACCESS__WH__SIS__USAGE
    comment = 'ウェアハウス {{ datacatalog_warehouse_name }} 向け利用権限'
;

grant role {{ sis_role_name_prefix }}_ACCESS__WH__SIS__USAGE to role {{ project_owner_role }};

grant usage on warehouse {{ datacatalog_warehouse_name }} to role {{ sis_role_name_prefix }}_ACCESS__WH__SIS__USAGE;
