-- noqa: disable=LT02

define role {{ sis_reader_role_name }}
    comment = 'Streamlit App 参照者向けロール'
;

grant role {{ sis_reader_role_name }} to role {{ project_owner_role }};

grant role {{ sis_role_name_prefix }}_ACCESS__WH__SIS__USAGE to role {{ sis_reader_role_name }};
