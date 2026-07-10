-- noqa: disable=LT02

define role {{ sis_role_prefix }}_ACCESS__TAG__DATA_CATEGORY__RO
    comment = 'タグ DATA_CATEGORY 向け参照権限'
;

grant role {{ sis_role_prefix }}_ACCESS__TAG__DATA_CATEGORY__RO to role {{ project_owner_role }};

grant usage on database {{ sis_database_name }} to role {{ sis_role_prefix }}_ACCESS__TAG__DATA_CATEGORY__RO;
grant usage on schema {{ sis_database_name }}.TAG to role {{ sis_role_prefix }}_ACCESS__TAG__DATA_CATEGORY__RO;

grant read on tag {{ sis_database_name }}.TAG.DATA_CATEGORY to role {{ sis_role_prefix }}_ACCESS__TAG__DATA_CATEGORY__RO;
