-- noqa: disable=LT02

define role {{ sis_role_prefix }}_FUNC_SIS_OWNER
    comment = 'Streamlit App 所有者向けロール'
;

grant role {{ sis_role_prefix }}_FUNC_SIS_OWNER to role {{ project_owner_role }};

-- account_usage 側を参照できれば、実際のデータベースは参照不要のはず
-- grant database role {{ sis_database_name }}.ACCESS__SCHEMA__DATA_AD__RO to role {{ sis_role_prefix }}_FUNC_SIS_OWNER;
-- grant database role {{ sis_database_name }}.ACCESS__SCHEMA__DATA_SALES__RO to role {{ sis_role_prefix }}_FUNC_SIS_OWNER;

grant role {{ sis_role_prefix }}_ACCESS__TAG__DATA_CATEGORY__RO to role {{ sis_role_prefix }}_FUNC_SIS_OWNER;
grant role {{ sis_role_prefix }}_ACCESS__TAG__DATA_DOMAIN__RO to role {{ sis_role_prefix }}_FUNC_SIS_OWNER;
grant role {{ sis_role_prefix }}_ACCESS__TAG__PII__RO to role {{ sis_role_prefix }}_FUNC_SIS_OWNER;
grant role {{ sis_role_prefix }}_ACCESS__TAG__SENSITIVITY__RO to role {{ sis_role_prefix }}_FUNC_SIS_OWNER;

grant role {{ sis_role_prefix }}_ACCESS__WH__SIS__USAGE to role {{ sis_role_prefix }}_FUNC_SIS_OWNER;

grant role {{ sis_role_prefix }}_ACCESS__STREAMLIT__CREATE to role {{ sis_role_prefix }}_FUNC_SIS_OWNER;

grant role {{ sis_role_prefix }}_ACCESS__INT__PYPI__USAGE to role {{ sis_role_prefix }}_FUNC_SIS_OWNER;
