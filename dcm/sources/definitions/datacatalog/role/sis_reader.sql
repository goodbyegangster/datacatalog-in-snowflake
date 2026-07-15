define role {{ sis_reader_role_name }}
    comment = 'Streamlit App 参照者向けロール'
;

grant role {{ sis_reader_role_name }} to role {{ datacatalog_owner_role_name }};

-- datacatalog データベース usage 権限
grant usage on database {{ datacatalog_database_name }} to role {{ sis_reader_role_name }};

-- datacatalog データベース内スキーマ usage 権限
grant usage on schema {{ datacatalog_database_name }}.APP to role {{ sis_reader_role_name }};
