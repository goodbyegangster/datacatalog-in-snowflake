-- noqa: disable=LT02

define role {{ sis_owner_role_name }}
    comment = 'Streamlit App 所有者向けロール'
;

grant role {{ sis_owner_role_name }} to role {{ project_owner_role }};

grant database role {{ datacatalog_database_name }}.ACCESS__SCHEMA__CATALOG__RO to role {{ sis_owner_role_name }};

grant role {{ sis_role_name_prefix }}_ACCESS__WH__SIS__USAGE to role {{ sis_owner_role_name }};

grant role {{ sis_role_name_prefix }}_ACCESS__STREAMLIT__CREATE to role {{ sis_owner_role_name }};

grant role {{ sis_role_name_prefix }}_ACCESS__INT__PYPI__USAGE to role {{ sis_owner_role_name }};
