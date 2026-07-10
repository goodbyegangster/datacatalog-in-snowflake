-- noqa: disable=LT02

-- 依存：CATALOG.ASSETS（先に refresh 済みであること）。

define procedure {{ sis_database_name }}.PROCEDURE.REFRESH_COLUMNS()
    returns string
    language sql
    execute as owner
as
$$
begin
    -- 制約情報をアカウント全体の SHOW から一時表へ退避
    show primary keys in account;
    create or replace temporary table {{ sis_database_name }}.CATALOG.TMP_PK as
        select
            "database_name" as db,
            "schema_name"   as sch,
            "table_name"    as tbl,
            "column_name"   as col
        from table(result_scan(last_query_id()));

    show unique keys in account;
    create or replace temporary table {{ sis_database_name }}.CATALOG.TMP_UK as
        select
            "database_name" as db,
            "schema_name"   as sch,
            "table_name"    as tbl,
            "column_name"   as col
        from table(result_scan(last_query_id()));

    show imported keys in account;
    create or replace temporary table {{ sis_database_name }}.CATALOG.TMP_FK as
        select
            "fk_database_name" as db,
            "fk_schema_name"   as sch,
            "fk_table_name"    as tbl,
            "fk_column_name"   as col,
            "pk_database_name" as ref_db,
            "pk_schema_name"   as ref_sch,
            "pk_table_name"    as ref_tbl,
            "pk_column_name"   as ref_col
        from table(result_scan(last_query_id()));

    create or replace table {{ sis_database_name }}.CATALOG.COLUMNS (
        TABLE_ID            comment '所属データ資産のキー',
        DATABASE_NAME       comment '階層_データベース',
        SCHEMA_NAME         comment '階層_スキーマ',
        TABLE_NAME          comment '所属データ資産名',
        COLUMN_NAME         comment '名前',
        ORDINAL_POSITION    comment '表示順',
        DATA_TYPE           comment 'データ型',
        DESCRIPTION         comment '説明',
        TAGS                comment 'タグ一覧。要素 object = {TAG_DATABASE, TAG_SCHEMA, TAG_NAME, TAG_VALUE}。なしは空配列',
        IS_PRIMARY_KEY      comment '制約_PRIMARY_KEY',
        IS_UNIQUE_KEY       comment '制約_UNIQUE',
        FOREIGN_KEYS        comment '制約_FOREIGN_KEY 参照先一覧。なしは空配列',
        IS_NULLABLE         comment '制約_NOT_NULL（false = NOT NULL）',
        MASKING_POLICY_NAME comment 'マスキングポリシー'
    ) as
    with cols as (
        select
            a.table_id,
            c.table_catalog,
            c.table_schema,
            c.table_name,
            c.column_name,
            c.ordinal_position,
            c.data_type,
            c.comment as description,
            c.is_nullable
        from snowflake.account_usage.columns as c
        inner join {{ sis_database_name }}.CATALOG.ASSETS as a
            on  a.database_name = c.table_catalog
            and a.schema_name   = c.table_schema
            and a.asset_name    = c.table_name
        where c.deleted is null
    ),
    ctags as (
        select
            d.object_database,
            d.object_schema,
            d.object_name,
            d.column_name,
            array_agg(object_construct(
                'TAG_DATABASE', d.tag_database,
                'TAG_SCHEMA',   d.tag_schema,
                'TAG_NAME',     d.tag_name,
                'TAG_VALUE',    d.tag_value
            )) as tags
        from (
            -- TAG_REFERENCES は同一タグを重複行で返すことがあるため重複排除
            select distinct
                tr.object_database,
                tr.object_schema,
                tr.object_name,
                tr.column_name,
                tr.tag_database,
                tr.tag_schema,
                tr.tag_name,
                tr.tag_value
            from snowflake.account_usage.tag_references as tr
            where tr.domain = 'COLUMN'
              and tr.column_name is not null
        ) as d
        group by d.object_database, d.object_schema, d.object_name, d.column_name
    ),
    mpol as (
        select
            pr.ref_database_name,
            pr.ref_schema_name,
            pr.ref_entity_name,
            pr.ref_column_name,
            pr.policy_name
        from snowflake.account_usage.policy_references as pr
        where pr.policy_kind = 'MASKING_POLICY'
          and pr.ref_column_name is not null
    ),
    fk as (
        select
            db, sch, tbl, col,
            array_agg(object_construct(
                'REFERENCED_DATABASE', ref_db,
                'REFERENCED_SCHEMA',   ref_sch,
                'REFERENCED_TABLE',    ref_tbl,
                'REFERENCED_COLUMN',   ref_col
            )) as foreign_keys
        from {{ sis_database_name }}.CATALOG.TMP_FK
        group by db, sch, tbl, col
    )
    select
        cols.table_id::number,
        cols.table_catalog::varchar(255),
        cols.table_schema::varchar(255),
        cols.table_name::varchar(255),
        cols.column_name::varchar(255),
        cols.ordinal_position::number,
        cols.data_type::varchar(255),
        cols.description::varchar,
        coalesce(ctags.tags, array_construct()),
        iff(pk.col is not null, true, false)::boolean,
        iff(uk.col is not null, true, false)::boolean,
        coalesce(fk.foreign_keys, array_construct()),
        (cols.is_nullable = 'YES')::boolean,
        mpol.policy_name::varchar(255)
    from cols
    left join {{ sis_database_name }}.CATALOG.TMP_PK as pk
        on pk.db = cols.table_catalog and pk.sch = cols.table_schema and pk.tbl = cols.table_name and pk.col = cols.column_name
    left join {{ sis_database_name }}.CATALOG.TMP_UK as uk
        on uk.db = cols.table_catalog and uk.sch = cols.table_schema and uk.tbl = cols.table_name and uk.col = cols.column_name
    left join fk
        on fk.db = cols.table_catalog and fk.sch = cols.table_schema and fk.tbl = cols.table_name and fk.col = cols.column_name
    left join ctags
        on  ctags.object_database = cols.table_catalog
        and ctags.object_schema   = cols.table_schema
        and ctags.object_name     = cols.table_name
        and ctags.column_name     = cols.column_name
    left join mpol
        on  mpol.ref_database_name = cols.table_catalog
        and mpol.ref_schema_name   = cols.table_schema
        and mpol.ref_entity_name   = cols.table_name
        and mpol.ref_column_name   = cols.column_name
    ;

    return 'CATALOG.COLUMNS refreshed';
end;
$$
;
