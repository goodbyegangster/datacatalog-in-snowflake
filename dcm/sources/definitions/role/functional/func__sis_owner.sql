-- noqa: disable=LT02

define role {{ sis_role_name_prefix }}_FUNC_SIS_OWNER
    comment = 'Streamlit App 所有者向けロール'
;

grant role {{ sis_role_name_prefix }}_FUNC_SIS_OWNER to role {{ project_owner_role }};

grant database role {{ sis_database_name }}.ACCESS__SCHEMA__CATALOG__RO to role {{ sis_role_name_prefix }}_FUNC_SIS_OWNER;

grant role {{ sis_role_name_prefix }}_ACCESS__WH__SIS__USAGE to role {{ sis_role_name_prefix }}_FUNC_SIS_OWNER;

grant role {{ sis_role_name_prefix }}_ACCESS__STREAMLIT__CREATE to role {{ sis_role_name_prefix }}_FUNC_SIS_OWNER;

grant role {{ sis_role_name_prefix }}_ACCESS__INT__PYPI__USAGE to role {{ sis_role_name_prefix }}_FUNC_SIS_OWNER;
