define role {{ datacatalog_owner_role_name }}
    comment = 'datacatalog オーナーロール'
;

grant role {{ datacatalog_owner_role_name }} to role {{ project_owner_role }};
