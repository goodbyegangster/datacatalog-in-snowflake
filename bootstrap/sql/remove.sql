use role ACCOUNTADMIN
;

-- PyPI 向けの external access を削除
drop external access integration if exists <% external_access_pypi_name %>
;

-- dcm project データベース 削除
drop database if exists <% dcm_database_name %>
;

-- dcm project owner role 削除
drop role if exists <% dcm_project_owner_role_name %>
;
