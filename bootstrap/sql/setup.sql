-- datacatalog owner role 作成
use role SECURITYADMIN;

create role if not exists <% datacatalog_owner_role_name %>
    comment = 'datacatalog owner role'
;

-- 作成した datacatalog ロールを SYSADMIN へ継承
grant role <% datacatalog_owner_role_name %> to role SYSADMIN;

-- Snowflake リソース作成権限を付与
use role ACCOUNTADMIN;
grant create compute pool on account
    to role <% datacatalog_owner_role_name %>
;
grant database role SNOWFLAKE.OBJECT_VIEWER
    to role <% datacatalog_owner_role_name %>
;
grant database role SNOWFLAKE.GOVERNANCE_VIEWER
    to role <% datacatalog_owner_role_name %>
;
grant execute task on account
    to role <% datacatalog_owner_role_name %>
;

use role SYSADMIN;
grant create database on account
    to role <% datacatalog_owner_role_name %>
;
grant create warehouse on account
    to role <% datacatalog_owner_role_name %>
;

use role SECURITYADMIN;
grant create role on account
    to role <% datacatalog_owner_role_name %>
;
grant manage visibility on account
    to role <% datacatalog_owner_role_name %>
;
grant manage grants on account
    to role <% datacatalog_owner_role_name %>
;

-- 作業者ユーザー向け datacatalog owner role を付与
grant role <% datacatalog_owner_role_name %>
    to user <% snowflake_my_user_name %>
;

-- dcm オブジェクトを格納するデータベース / スキーマを作成
use role <% datacatalog_owner_role_name %>
;

create database if not exists <% dcm_database_name %>
    data_retention_time_in_days = 0
    comment = 'dcm database (datacatalog 向け)'
;

create schema if not exists <% dcm_database_name %>.DCM
    comment = 'dcm object schema'
;

-- PyPI 向けの external access を削除
use role ACCOUNTADMIN;

create or replace external access integration <% external_access_pypi_name %>
    allowed_network_rules = (snowflake.external_access.pypi_rule)
    enabled = TRUE
    comment = 'PyPI アクセス用 (datacatalog 向け)'
;
