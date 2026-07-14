-- FULL_NAME 用ポリシーを作成
create masking policy if not exists <% datacatalog_database_name %>.POLICY.MASK_FULL_NAME as (VAL STRING) returns string ->
case
    when current_role() in ('ACCOUNTADMIN') then VAL
    else '*** MASKED ***'
end
;

-- EMAIL 用ポリシーを作成
create masking policy if not exists <% datacatalog_database_name %>.POLICY.MASK_EMAIL as (VAL STRING) returns string ->
case
    when current_role() in ('ACCOUNTADMIN') then VAL
    else regexp_replace(VAL, '.+\\@', '*****@')
end
;

-- FULL_NAME カラムに適用
alter table <% datacatalog_database_name %>.DATA_AD.CAMPAIGN_LEADS
modify column FULL_NAME set masking policy <% datacatalog_database_name %>.POLICY.MASK_FULL_NAME
;

-- EMAIL カラムに適用
alter table <% datacatalog_database_name %>.DATA_AD.CAMPAIGN_LEADS
modify column EMAIL set masking policy <% datacatalog_database_name %>.POLICY.MASK_EMAIL
;
