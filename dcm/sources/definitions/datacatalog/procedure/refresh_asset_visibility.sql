-- ACCESS_EDGES を再帰的に辿り、User↔Asset の閲覧可否（展開済みペア）を生成する。
-- 依存：CATALOG.ACCESS_EDGES / CATALOG.ASSETS（先に refresh 済みであること）。

define procedure {{ datacatalog_database_name }}.PROCEDURE.REFRESH_ASSET_VISIBILITY()
    returns string
    language sql
    comment = 'ASSET_VISIBILITY テーブル洗替処理'
    execute as owner
as
$$
begin
    create or replace table {{ datacatalog_database_name }}.CATALOG.ASSET_VISIBILITY (
        USER_NAME     comment '閲覧可能ユーザー名',
        TABLE_ID      comment '閲覧可能データ資産のキー',
        DATABASE_NAME comment '対象資産の階層_データベース',
        SCHEMA_NAME   comment '対象資産の階層_スキーマ',
        ASSET_NAME    comment '対象資産名',
        USER_ROLES    comment 'user に直接付与された role 名一覧',
        ASSET_ROLES   comment 'asset に直接権限を持つ role / database role 名一覧'
    ) as
    with recursive reach as (
        -- 起点：user -> 直下ロール（first_role = 1 hop ロール）
        select
            e.source_node as user_name,
            e.target_node as role_node,
            e.target_node as first_role
        from {{ datacatalog_database_name }}.CATALOG.ACCESS_EDGES as e
        where e.relation_type = 'USER_TO_ROLE'

        union all

        -- 継承：role -> role / role -> database role（全段）
        select
            r.user_name,
            e.target_node as role_node,
            r.first_role
        from reach as r
        inner join {{ datacatalog_database_name }}.CATALOG.ACCESS_EDGES as e
            on  e.relation_type = 'ROLE_TO_ROLE'
            and e.source_node   = r.role_node
    ),
    asset_grant as (
        -- ロール（アカウント/DB）が直接 SELECT / OWNERSHIP を持つ資産
        select
            e.source_node as role_node,
            a.table_id,
            a.database_name,
            a.schema_name,
            a.asset_name
        from {{ datacatalog_database_name }}.CATALOG.ACCESS_EDGES as e
        inner join {{ datacatalog_database_name }}.CATALOG.ASSETS as a
            on (a.database_name || '.' || a.schema_name || '.' || a.asset_name) = e.target_node
        where e.relation_type = 'ROLE_TO_ASSET'
    )
    select
        r.user_name::varchar(255),
        ag.table_id::number,
        ag.database_name::varchar(255),
        ag.schema_name::varchar(255),
        ag.asset_name::varchar(255),
        array_agg(distinct r.first_role),
        array_agg(distinct ag.role_node)
    from reach as r
    inner join asset_grant as ag
        on ag.role_node = r.role_node
    group by r.user_name, ag.table_id, ag.database_name, ag.schema_name, ag.asset_name
    ;

    return 'CATALOG.ASSET_VISIBILITY refreshed';
end;
$$
;
