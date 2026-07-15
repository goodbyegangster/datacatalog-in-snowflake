-- masking policy を削除
drop masking policy if exists <% datacatalog_database_name %>.SAMPLE_POLICY.MASK_FULL_NAME;
drop masking policy if exists <% datacatalog_database_name %>.SAMPLE_POLICY.MASK_EMAIL;
