-- dcm project owner role 作成
use role SECURITYADMIN;

create role if not exists <% dcm_project_owner_role_name %>
comment = 'dcm project owner role'
;

grant role <% dcm_project_owner_role_name %> to role SYSADMIN
;

-- dcm で管理する Snowflake リソース作成権限を付与
use role ACCOUNTADMIN
;
grant create compute pool on account to role <% dcm_project_owner_role_name %>
;
grant database role SNOWFLAKE.OBJECT_VIEWER to role <% dcm_project_owner_role_name %>
;
grant database role SNOWFLAKE.GOVERNANCE_VIEWER to role <% dcm_project_owner_role_name %>
;

use role SYSADMIN ;
grant create database on account to role <% dcm_project_owner_role_name %>
;
grant create warehouse on account to role <% dcm_project_owner_role_name %>
;

use role SECURITYADMIN
;
grant create role on account to role <% dcm_project_owner_role_name %>
;
grant manage visibility on account to role <% dcm_project_owner_role_name %>
;
grant manage grants on account to role <% dcm_project_owner_role_name %>
;

-- 作業者ユーザー向け dcm project owner role を付与
grant role <% dcm_project_owner_role_name %> to user <% SNOWFLAKE_MY_USER_NAME %>
;

-- dcm オブジェクトを格納するデータベース / スキーマを作成
use role <% dcm_project_owner_role_name %>
;

create database if not exists <% dcm_database_name %>
data_retention_time_in_days = 0
comment = 'dcm object database'
;

create schema if not exists <% dcm_database_name %>.DCM
comment = 'dcm object schema'
;

-- PyPI 向けの external access を削除
use role ACCOUNTADMIN
;

create or replace external access integration <% external_access_pypi_name %>
allowed_network_rules = (snowflake.external_access.pypi_rule)
enabled = TRUE
comment = 'PyPI アクセス用'
;
