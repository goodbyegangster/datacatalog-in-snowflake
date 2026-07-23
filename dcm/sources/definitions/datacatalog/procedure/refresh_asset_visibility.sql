-- ユーザーと閲覧可能な資産のペアを、ユーザーへの直接付与ロールと資産に直接権限を持つロールとともに生成する。

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
    with recursive
    -- ACCESS_EDGES よりユーザーに直接付与されたロールから継承関係を辿り、到達可能なロールを展開したデータをつくる
    -- Snowflake では循環するロール階層を設定できないため、この再帰 CTE では循環検知を行わない
    reach (USER_NAME, ROLE_NODE, FIRST_ROLE) as (
        -- ユーザーに直接付与されたロールを、継承探索の起点と FIRST_ROLE に設定する
        select
            e.SOURCE_NODE as USER_NAME,
            e.TARGET_NODE as ROLE_NODE,
            e.TARGET_NODE as FIRST_ROLE
        from {{ datacatalog_database_name }}.CATALOG.ACCESS_EDGES as e
        where e.RELATION_TYPE = 'USER_TO_ROLE'

        union all

        -- ROLE_TO_ROLE を辿り、ユーザーが権限を継承できるロールをすべて展開する
        select
            r.USER_NAME,
            e.TARGET_NODE as ROLE_NODE,
            r.FIRST_ROLE
        from reach as r
        inner join {{ datacatalog_database_name }}.CATALOG.ACCESS_EDGES as e
            on  e.RELATION_TYPE = 'ROLE_TO_ROLE'
            and e.SOURCE_NODE   = r.ROLE_NODE
    ),

    -- ASSETS の識別子を ACCESS_EDGES と同じ引用規則で変換し、ノード名の照合に使う asset_nodes とする
    asset_nodes as (
        select
            TABLE_ID,
            DATABASE_NAME,
            SCHEMA_NAME,
            ASSET_NAME,
            -- 二重引用符で囲む識別子に含まれる引用符は、識別子の一部として扱えるよう二重化する
            (
                iff(
                    contains(DATABASE_NAME, '.') or contains(DATABASE_NAME, '"'),
                    '"' || replace(DATABASE_NAME, '"', '""') || '"',
                    DATABASE_NAME
                )
                || '.'
                || iff(
                    contains(SCHEMA_NAME, '.') or contains(SCHEMA_NAME, '"'),
                    '"' || replace(SCHEMA_NAME, '"', '""') || '"',
                    SCHEMA_NAME
                )
                || '.'
                || iff(
                    contains(ASSET_NAME, '.') or contains(ASSET_NAME, '"'),
                    '"' || replace(ASSET_NAME, '"', '""') || '"',
                    ASSET_NAME
                )
            ) as ASSET_NODE
        from {{ datacatalog_database_name }}.CATALOG.ASSETS
    ),

    -- ACCESS_EDGES と asset_nodes を照合し、資産に対する権限を直接付与されたロールと資産のペアを asset_grant とする
    asset_grant as (
        select
            e.SOURCE_NODE  as ROLE_NODE,
            a.TABLE_ID     as TABLE_ID,
            a.DATABASE_NAME,
            a.SCHEMA_NAME,
            a.ASSET_NAME
        from {{ datacatalog_database_name }}.CATALOG.ACCESS_EDGES as e
        inner join asset_nodes as a
            on a.ASSET_NODE = e.TARGET_NODE
        where e.RELATION_TYPE = 'ROLE_TO_ASSET'
    ),

    -- reach と asset_grant から閲覧可能なユーザーと資産のペアを作り、双方の直接付与ロールを集約して catalog_asset_visibility とする
    catalog_asset_visibility as (
        select
            r.USER_NAME::varchar(255)     as USER_NAME,
            ag.TABLE_ID::number           as TABLE_ID,
            ag.DATABASE_NAME::varchar(255) as DATABASE_NAME,
            ag.SCHEMA_NAME::varchar(255)   as SCHEMA_NAME,
            ag.ASSET_NAME::varchar(255)    as ASSET_NAME,
            array_agg(distinct r.FIRST_ROLE) within group (order by r.FIRST_ROLE) as USER_ROLES,
            array_agg(distinct ag.ROLE_NODE) within group (order by ag.ROLE_NODE) as ASSET_ROLES
        from reach as r
        inner join asset_grant as ag
            on ag.ROLE_NODE = r.ROLE_NODE
        group by
            r.USER_NAME,
            ag.TABLE_ID,
            ag.DATABASE_NAME,
            ag.SCHEMA_NAME,
            ag.ASSET_NAME
    )
    select
        USER_NAME,
        TABLE_ID,
        DATABASE_NAME,
        SCHEMA_NAME,
        ASSET_NAME,
        USER_ROLES,
        ASSET_ROLES
    from catalog_asset_visibility
    ;

    return 'CATALOG.ASSET_VISIBILITY refreshed';
end;
$$
;
