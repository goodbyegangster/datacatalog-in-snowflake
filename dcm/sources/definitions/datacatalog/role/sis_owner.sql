define role {{ sis_owner_role_name }}
    comment = 'Streamlit App 所有者向けロール'
;

grant role {{ sis_owner_role_name }} to role {{ datacatalog_owner_role_name }};

-- datacatalog データベース usage 権限
grant usage on database {{ datacatalog_database_name }} to role {{ sis_owner_role_name }};

-- datacatalog データベース内スキーマ usage 権限
grant usage on schema {{ datacatalog_database_name }}.APP to role {{ sis_owner_role_name }};
grant usage on schema {{ datacatalog_database_name }}.CATALOG to role {{ sis_owner_role_name }};

-- datacatalog.catalog スキーマ select 権限
grant select, references on all tables in schema {{ datacatalog_database_name }}.CATALOG
    to role {{ sis_owner_role_name }}
;
grant select, references on future tables in schema {{ datacatalog_database_name }}.CATALOG
    to role {{ sis_owner_role_name }}
;

-- streamlit app 作成権限
grant create streamlit on schema {{ datacatalog_database_name }}.APP to role {{ sis_owner_role_name }};

-- ウェアハウス usage 権限
grant usage on warehouse {{ datacatalog_warehouse_name }} to role {{ sis_owner_role_name }};

-- external integration 利用権限
grant usage on integration {{ external_access_pypi_name }} to role {{ sis_owner_role_name }};
