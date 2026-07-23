define procedure {{ datacatalog_database_name }}.PROCEDURE.REFRESH_ACCESS_EDGES()
    returns string
    language sql
    comment = 'ACCESS_EDGES テーブル洗替処理'
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
    with
    -- GRANTS_TO_ROLES の識別子内にあるピリオドや引用符をノードの構文と区別できる表記へ変換し、role_grants とする
    role_grants as (
        select
            deleted_on,
            granted_to,
            granted_on,
            privilege,
            grantee_name,
            table_catalog,
            table_schema,
            name,
            -- 二重引用符で囲む識別子に含まれる引用符は、識別子の一部として扱えるよう二重化する
            iff(
                contains(grantee_name, '.') or contains(grantee_name, '"'),
                '"' || replace(grantee_name, '"', '""') || '"',
                grantee_name
            ) as GRANTEE_IDENTIFIER,
            iff(
                contains(table_catalog, '.') or contains(table_catalog, '"'),
                '"' || replace(table_catalog, '"', '""') || '"',
                table_catalog
            ) as DATABASE_IDENTIFIER,
            iff(
                contains(table_schema, '.') or contains(table_schema, '"'),
                '"' || replace(table_schema, '"', '""') || '"',
                table_schema
            ) as SCHEMA_IDENTIFIER,
            iff(
                contains(name, '.') or contains(name, '"'),
                '"' || replace(name, '"', '""') || '"',
                name
            ) as NAME_IDENTIFIER
        from SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
    ),

    -- GRANTS_TO_USERS と USERS から直接付与を抽出し、内部概念 USER_TO_ACCOUNT_ROLE のエッジとする
    user_to_account_role_edges as (
        select
            gu.grantee_name::varchar as SOURCE_NODE,
            'USER'::varchar          as SOURCE_TYPE,
            -- ロール名内のピリオドや引用符をノードの構文と区別するため、該当する識別子だけ二重引用符で囲む
            iff(
                contains(gu.role, '.') or contains(gu.role, '"'),
                '"' || replace(gu.role, '"', '""') || '"',
                gu.role
            )::varchar                as TARGET_NODE,
            'ROLE'::varchar          as TARGET_TYPE,
            null::varchar            as PRIVILEGE,
            'ROLE'::varchar          as GRANTED_ON
        from SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS as gu
        inner join {{ datacatalog_database_name }}.CATALOG.USERS as u
            on u.USER_NAME = gu.grantee_name
        where gu.deleted_on is null
          and gu.role <> 'PUBLIC'
    ),

    -- role_grants と USERS から直接付与を抽出し、内部概念 USER_TO_DATABASE_ROLE のエッジとする
    user_to_database_role_edges as (
        select
            gr.grantee_name::varchar                                as SOURCE_NODE,
            'USER'::varchar                                         as SOURCE_TYPE,
            (gr.DATABASE_IDENTIFIER || '.' || gr.NAME_IDENTIFIER)::varchar
                                                                    as TARGET_NODE,
            'DATABASE_ROLE'::varchar                                as TARGET_TYPE,
            gr.privilege::varchar                                   as PRIVILEGE,
            gr.granted_on::varchar                                  as GRANTED_ON
        from role_grants as gr
        inner join {{ datacatalog_database_name }}.CATALOG.USERS as u
            on u.USER_NAME = gr.grantee_name
        where gr.deleted_on is null
          and gr.granted_to = 'USER'
          and gr.granted_on = 'DATABASE_ROLE'
          and gr.privilege = 'USAGE'
    ),

    -- USER_TO_ACCOUNT_ROLE と USER_TO_DATABASE_ROLE を統合し、direct_user_role_edges とする
    direct_user_role_edges as (
        select
            SOURCE_NODE,
            SOURCE_TYPE,
            TARGET_NODE,
            TARGET_TYPE,
            PRIVILEGE,
            GRANTED_ON
        from user_to_account_role_edges

        union all

        select
            SOURCE_NODE,
            SOURCE_TYPE,
            TARGET_NODE,
            TARGET_TYPE,
            PRIVILEGE,
            GRANTED_ON
        from user_to_database_role_edges
    ),

    -- direct_user_role_edges の内部概念を、公開用の関係 USER_TO_ROLE にそろえて user_to_role_edges とする
    user_to_role_edges as (
        select
            SOURCE_NODE,
            SOURCE_TYPE,
            TARGET_NODE,
            TARGET_TYPE,
            'USER_TO_ROLE'::varchar as RELATION_TYPE,
            PRIVILEGE,
            GRANTED_ON
        from direct_user_role_edges
    ),

    -- GRANTS_TO_ROLES から有効なロール継承関係を抽出し、向きをそろえた role_to_role_edges とする
    role_to_role_edges as (
        select
            iff(
                granted_to = 'DATABASE_ROLE',
                DATABASE_IDENTIFIER || '.' || GRANTEE_IDENTIFIER,
                GRANTEE_IDENTIFIER
            )::varchar                              as SOURCE_NODE,
            iff(
                granted_to = 'DATABASE_ROLE',
                'DATABASE_ROLE',
                'ROLE'
            )::varchar                              as SOURCE_TYPE,
            iff(
                granted_on = 'DATABASE_ROLE',
                DATABASE_IDENTIFIER || '.' || NAME_IDENTIFIER,
                NAME_IDENTIFIER
            )::varchar                              as TARGET_NODE,
            granted_on::varchar                     as TARGET_TYPE,
            'ROLE_TO_ROLE'::varchar                 as RELATION_TYPE,
            privilege::varchar                      as PRIVILEGE,
            granted_on::varchar                     as GRANTED_ON
        from role_grants
        where deleted_on is null
          and granted_on in ('ROLE', 'DATABASE_ROLE')
          -- ドキュメント上は 'ACCOUNT ROLE' という値が記載されているが、実際に格納されている値は 'ROLE' になる
          -- NOTE: https://docs.snowflake.com/en/sql-reference/account-usage/grants_to_roles
          and granted_to in ('ROLE', 'DATABASE_ROLE')
          -- OWNERSHIP は所有権を示すため、ロールの継承関係を表す USAGE のみを対象とする
          and privilege = 'USAGE'
          and grantee_name <> 'PUBLIC'
          and name <> 'PUBLIC'
    ),

    -- GRANTS_TO_ROLES と ASSETS から収集対象資産への直接権限を抽出し、role_to_asset_edges とする
    role_to_asset_edges as (
        select
            iff(
                gr.granted_to = 'DATABASE_ROLE',
                gr.DATABASE_IDENTIFIER || '.' || gr.GRANTEE_IDENTIFIER,
                gr.GRANTEE_IDENTIFIER
            )::varchar                                            as SOURCE_NODE,
            iff(
                gr.granted_to = 'DATABASE_ROLE',
                'DATABASE_ROLE',
                'ROLE'
            )::varchar                                            as SOURCE_TYPE,
            (
                gr.DATABASE_IDENTIFIER
                || '.'
                || gr.SCHEMA_IDENTIFIER
                || '.'
                || gr.NAME_IDENTIFIER
            )::varchar                                            as TARGET_NODE,
            gr.granted_on::varchar                                as TARGET_TYPE,
            'ROLE_TO_ASSET'::varchar                              as RELATION_TYPE,
            gr.privilege::varchar                                 as PRIVILEGE,
            gr.granted_on::varchar                                as GRANTED_ON
        from role_grants as gr
        inner join {{ datacatalog_database_name }}.CATALOG.ASSETS as a
            on  a.DATABASE_NAME = gr.table_catalog
            and a.SCHEMA_NAME   = gr.table_schema
            and a.ASSET_NAME    = gr.name
        where gr.deleted_on is null
          and gr.granted_on in ('TABLE', 'VIEW', 'MATERIALIZED VIEW', 'EXTERNAL TABLE')
          and gr.privilege in ('SELECT', 'OWNERSHIP')
          and gr.granted_to in ('ROLE', 'DATABASE_ROLE')
          and gr.grantee_name <> 'PUBLIC'
    ),

    -- 3種類のエッジを統合し、ACCESS_EDGES の最終出力となる catalog_access_edges とする
    catalog_access_edges as (
        select
            SOURCE_NODE,
            SOURCE_TYPE,
            TARGET_NODE,
            TARGET_TYPE,
            RELATION_TYPE,
            PRIVILEGE,
            GRANTED_ON
        from user_to_role_edges

        union all

        select
            SOURCE_NODE,
            SOURCE_TYPE,
            TARGET_NODE,
            TARGET_TYPE,
            RELATION_TYPE,
            PRIVILEGE,
            GRANTED_ON
        from role_to_role_edges

        union all

        select
            SOURCE_NODE,
            SOURCE_TYPE,
            TARGET_NODE,
            TARGET_TYPE,
            RELATION_TYPE,
            PRIVILEGE,
            GRANTED_ON
        from role_to_asset_edges
    )
    select
        SOURCE_NODE,
        SOURCE_TYPE,
        TARGET_NODE,
        TARGET_TYPE,
        RELATION_TYPE,
        PRIVILEGE,
        GRANTED_ON
    from catalog_access_edges
    ;

    return 'CATALOG.ACCESS_EDGES refreshed';
end;
$$
;
