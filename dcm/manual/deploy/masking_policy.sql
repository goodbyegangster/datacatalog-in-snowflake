-- noqa: disable=LT02

-- FULL_NAME 用ポリシーを作成
create masking policy if not exists <% sis_database_name %>.POLICY.MASK_FULL_NAME as (val string) returns string ->
    case
        when current_role() in ('ACCOUNTADMIN') then val
        else '*** MASKED ***'
    end
;

-- EMAIL 用ポリシーを作成
create masking policy if not exists <% sis_database_name %>.POLICY.MASK_EMAIL as (val string) returns string ->
    case
        when current_role() in ('ACCOUNTADMIN') then val
        else regexp_replace(val, '.+\\@', '*****@')
    end
;

-- FULL_NAME カラムに適用
alter table <% sis_database_name %>.DATA_AD.CAMPAIGN_LEADS
    modify column FULL_NAME set masking policy <% sis_database_name %>.POLICY.MASK_FULL_NAME
;

-- EMAIL カラムに適用
alter table <% sis_database_name %>.DATA_AD.CAMPAIGN_LEADS
    modify column EMAIL set masking policy <% sis_database_name %>.POLICY.MASK_EMAIL
;
