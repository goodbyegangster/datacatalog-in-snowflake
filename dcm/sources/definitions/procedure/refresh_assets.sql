-- noqa: disable=LT02

define procedure {{ sis_database_name }}.PROCEDURE.REFRESH_ASSETS()
    returns string
    language sql
    execute as owner
as
$$
begin
    create or replace table {{ sis_database_name }}.CATALOG.ASSETS (
        TABLE_ID                    comment 'データ資産の一意キー',
        DATABASE_NAME               comment '階層_データベース',
        SCHEMA_NAME                 comment '階層_スキーマ',
        ASSET_NAME                  comment '名前',
        ASSET_TYPE                  comment 'オブジェクト種類',
        DESCRIPTION                 comment '説明',
        ROW_COUNT                   comment '統計情報_行数（ROW_COUNT）',
        BYTES                       comment '統計情報_データサイズ（BYTES）',
        TAGS                        comment 'タグ一覧。要素 object = {TAG_DATABASE, TAG_SCHEMA, TAG_NAME, TAG_VALUE}。なしは空配列',
        CONTACT_STEWARD             comment '連絡先_スチュワード',
        CONTACT_SUPPORT             comment '連絡先_サポート',
        CONTACT_ACCESS_APPROVAL     comment '連絡先_承認者',
        CONTACT_SECURITY_COMPLIANCE comment '連絡先_セキュリティとコンプライアンス',
        IS_PUBLIC_VISIBILITY        comment 'PUBLIC ロールに OWNERSHIP/SELECT があり全ユーザーが参照可能なら true'
    ) as
    with base as (
        select
            t.table_id,
            t.table_catalog as database_name,
            t.table_schema  as schema_name,
            t.table_name    as asset_name,
            case
                when t.is_dynamic = 'YES' then 'DYNAMIC TABLE'
                when t.is_iceberg = 'YES' then 'ICEBERG TABLE'
                when t.is_hybrid  = 'YES' then 'HYBRID TABLE'
                else t.table_type
            end             as asset_type,
            t.comment       as description,
            t.row_count,
            t.bytes
        from snowflake.account_usage.tables as t
        inner join snowflake.account_usage.databases as d
            on d.database_name = t.table_catalog
        where t.deleted is null
            and d.deleted is null
            and d.type = 'STANDARD'
    ),
    tags as (
        select
            d.object_database,
            d.object_schema,
            d.object_name,
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
                tr.tag_database,
                tr.tag_schema,
                tr.tag_name,
                tr.tag_value
            from snowflake.account_usage.tag_references as tr
            where tr.domain = 'TABLE'
                and tr.column_name is null
        ) as d
        group by d.object_database, d.object_schema, d.object_name
    ),
    contacts as (
        select
            cr.object_database,
            cr.object_schema,
            cr.object_name,
            max(iff(cr.contact_purpose = 'STEWARD',             cr.contact_name, null)) as contact_steward,
            max(iff(cr.contact_purpose = 'SUPPORT',             cr.contact_name, null)) as contact_support,
            max(iff(cr.contact_purpose = 'ACCESS_APPROVAL',     cr.contact_name, null)) as contact_access_approval,
            max(iff(cr.contact_purpose = 'SECURITY_COMPLIANCE', cr.contact_name, null)) as contact_security_compliance
        from snowflake.account_usage.contact_references as cr
        group by cr.object_database, cr.object_schema, cr.object_name
    ),
    public_vis as (
        select distinct
            g.table_catalog as database_name,
            g.table_schema  as schema_name,
            g.name          as object_name
        from snowflake.account_usage.grants_to_roles as g
        where g.deleted_on is null
          and g.grantee_name = 'PUBLIC'
          and g.granted_on in ('TABLE', 'VIEW', 'MATERIALIZED VIEW')
          and g.privilege in ('SELECT', 'OWNERSHIP')
    )
    select
        base.table_id::number,
        base.database_name::varchar(255),
        base.schema_name::varchar(255),
        base.asset_name::varchar(255),
        base.asset_type::varchar(50),
        base.description::varchar,
        base.row_count::number,
        base.bytes::number,
        coalesce(tags.tags, array_construct()),
        contacts.contact_steward::varchar(255),
        contacts.contact_support::varchar(255),
        contacts.contact_access_approval::varchar(255),
        contacts.contact_security_compliance::varchar(255),
        (public_vis.object_name is not null)::boolean
    from base
    left join tags
        on  tags.object_database = base.database_name
        and tags.object_schema   = base.schema_name
        and tags.object_name     = base.asset_name
    left join contacts
        on  contacts.object_database = base.database_name
        and contacts.object_schema   = base.schema_name
        and contacts.object_name     = base.asset_name
    left join public_vis
        on  public_vis.database_name = base.database_name
        and public_vis.schema_name   = base.schema_name
        and public_vis.object_name   = base.asset_name
    ;

    return 'CATALOG.ASSETS refreshed';
end;
$$
;
