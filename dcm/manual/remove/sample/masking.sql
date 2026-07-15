-- FULL_NAME カラムよりポリシーを削除
alter table <% datacatalog_database_name %>.SAMPLE_DATA_AD.CAMPAIGN_LEADS
    alter column FULL_NAME unset masking policy
;

-- EMAIL カラムよりポリシーを削除
alter table <% datacatalog_database_name %>.SAMPLE_DATA_AD.CAMPAIGN_LEADS
    alter column EMAIL unset masking policy
;

-- masking policy そのものを削除
drop masking policy if exists <% datacatalog_database_name %>.SAMPLE_POLICY.MASK_FULL_NAME;
drop masking policy if exists <% datacatalog_database_name %>.SAMPLE_POLICY.MASK_EMAIL;
