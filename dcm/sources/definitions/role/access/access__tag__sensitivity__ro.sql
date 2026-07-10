-- noqa: disable=LT02

define role {{ sis_role_prefix }}_ACCESS__TAG__SENSITIVITY__RO
    comment = 'タグ SENSITIVITY 向け参照権限'
;

grant role {{ sis_role_prefix }}_ACCESS__TAG__SENSITIVITY__RO to role {{ project_owner_role }};

grant usage on database {{ sis_database_name }} to role {{ sis_role_prefix }}_ACCESS__TAG__SENSITIVITY__RO;
grant usage on schema {{ sis_database_name }}.TAG to role {{ sis_role_prefix }}_ACCESS__TAG__SENSITIVITY__RO;

grant read on tag {{ sis_database_name }}.TAG.SENSITIVITY to role {{ sis_role_prefix }}_ACCESS__TAG__SENSITIVITY__RO;
