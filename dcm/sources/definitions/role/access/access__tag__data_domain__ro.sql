-- noqa: disable=LT02

define role {{ sis_role_name_prefix }}_ACCESS__TAG__DATA_DOMAIN__RO
    comment = 'タグ DATA_DOMAIN 向け参照権限'
;

grant role {{ sis_role_name_prefix }}_ACCESS__TAG__DATA_DOMAIN__RO to role {{ project_owner_role }};

grant usage on database {{ datacatalog_database_name }} to role {{ sis_role_name_prefix }}_ACCESS__TAG__DATA_DOMAIN__RO;
grant usage on schema {{ datacatalog_database_name }}.TAG to role {{ sis_role_name_prefix }}_ACCESS__TAG__DATA_DOMAIN__RO;

grant read on tag {{ datacatalog_database_name }}.TAG.DATA_DOMAIN to role {{ sis_role_name_prefix }}_ACCESS__TAG__DATA_DOMAIN__RO;
