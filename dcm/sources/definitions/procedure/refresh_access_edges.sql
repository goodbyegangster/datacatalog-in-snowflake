-- noqa: disable=LT02

define procedure {{ datacatalog_database_name }}.PROCEDURE.REFRESH_ACCESS_EDGES()
    returns string
    language sql
    execute as owner
as
$$
begin
    create or replace table {{ datacatalog_database_name }}.CATALOG.ACCESS_EDGES (
        SOURCE_NODE   comment '接続元ノード名（ユーザー名 / ロール名 / DBロールは DB.ROLE / アセットは FQN）',
        SOURCE_TYPE   comment '接続元タイプ（USER / ROLE / DATABASE_ROLE）',
        TARGET_NODE   comment '接続先ノード名（同上の命名規則）',
        TARGET_TYPE   comment '接続先タイプ（ROLE / DATABASE_ROLE / TABLE / VIEW / DYNAMIC TABLE 等）',
        RELATION_TYPE comment '関係の種類（USER_TO_ROLE / ROLE_TO_ROLE / ROLE_TO_ASSET）。source/target から導出の派生列',
        PRIVILEGE     comment '付与権限（SELECT / OWNERSHIP 等。ロール付与は USAGE、NULL 可）',
        GRANTED_ON    comment 'ACCOUNT_USAGE.GRANTS_TO_ROLES 由来の GRANTED_ON 値'
    ) as
    -- USER_TO_ROLE：収集対象ユーザーに直接付与されたロール
    select
        gu.grantee_name::varchar(255) as source_node,
        'USER'::varchar(20)           as source_type,
        gu.role::varchar(255)         as target_node,
        'ROLE'::varchar(20)           as target_type,
        'USER_TO_ROLE'::varchar(20)   as relation_type,
        null::varchar(50)             as privilege,
        'ROLE'::varchar(50)           as granted_on
    from snowflake.account_usage.grants_to_users as gu
    inner join {{ datacatalog_database_name }}.CATALOG.USERS as u
        on u.user_name = gu.grantee_name
    where gu.deleted_on is null
      and gu.role <> 'PUBLIC'

    union all

    -- ROLE_TO_ROLE：ロール／データベースロールの membership（アクセスは source -> target に流れる）
    -- USAGE のみ（ロールの OWNERSHIP は「所有」であって継承ではないため除外）。
    -- DB ロールは DB 内でしか一意でないため table_catalog で DB 修飾する。
    select
        iff(gr.granted_to = 'DATABASE_ROLE', gr.table_catalog || '.' || gr.grantee_name, gr.grantee_name)::varchar(255),
        iff(gr.granted_to = 'DATABASE_ROLE', 'DATABASE_ROLE', 'ROLE')::varchar(20),
        iff(gr.granted_on = 'DATABASE_ROLE', gr.table_catalog || '.' || gr.name, gr.name)::varchar(255),
        gr.granted_on::varchar(20),
        'ROLE_TO_ROLE'::varchar(20),
        gr.privilege::varchar(50),
        gr.granted_on::varchar(50)
    from snowflake.account_usage.grants_to_roles as gr
    where gr.deleted_on is null
      and gr.granted_on in ('ROLE', 'DATABASE_ROLE')
      and gr.granted_to in ('ROLE', 'DATABASE_ROLE')
      and gr.privilege = 'USAGE'
      and gr.grantee_name <> 'PUBLIC'
      and gr.name <> 'PUBLIC'

    union all

    -- ROLE_TO_ASSET：資産への SELECT / OWNERSHIP（収集対象資産のみ、PUBLIC は除外）
    select
        iff(gr.granted_to = 'DATABASE_ROLE', gr.table_catalog || '.' || gr.grantee_name, gr.grantee_name)::varchar(255),
        iff(gr.granted_to = 'DATABASE_ROLE', 'DATABASE_ROLE', 'ROLE')::varchar(20),
        (gr.table_catalog || '.' || gr.table_schema || '.' || gr.name)::varchar(255),
        gr.granted_on::varchar(20),
        'ROLE_TO_ASSET'::varchar(20),
        gr.privilege::varchar(50),
        gr.granted_on::varchar(50)
    from snowflake.account_usage.grants_to_roles as gr
    inner join {{ datacatalog_database_name }}.CATALOG.ASSETS as a
        on  a.database_name = gr.table_catalog
        and a.schema_name   = gr.table_schema
        and a.asset_name    = gr.name
    where gr.deleted_on is null
        and gr.granted_on in ('TABLE', 'VIEW', 'MATERIALIZED VIEW', 'EXTERNAL TABLE')
        and gr.privilege in ('SELECT', 'OWNERSHIP')
        and gr.granted_to in ('ROLE', 'DATABASE_ROLE')
        and gr.grantee_name <> 'PUBLIC'
    ;

    return 'CATALOG.ACCESS_EDGES refreshed';
end;
$$
;
