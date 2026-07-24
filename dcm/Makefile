.DEFAULT_GOAL := help

include $(dir $(lastword $(MAKEFILE_LIST)))../.env

.PHONY: help
help:
	@printf "%-30s %-60s\n" "[Sub command]" "[Description]"
	@grep -hE '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "%-30s %-60s\n", $$1, $$2}'

.PHONY: init-manifest-yml
init-manifest-yml: ## .env から manifest.yml を生成する
	bash ./scripts/init-manifest-yml.sh

.PHONY: dcm-create
dcm-create: ## DCM プロジェクトを作成する
	snow dcm create -c $(SNOWFLAKE_CLI_CONNECTION_NAME) --role $(DATACATALOG_OWNER_ROLE_NAME)

.PHONY: dcm-plan
dcm-plan: ## デプロイ内容の差分を確認する
	snow dcm plan -c $(SNOWFLAKE_CLI_CONNECTION_NAME) --role $(DATACATALOG_OWNER_ROLE_NAME)

.PHONY: dcm-plan-detail
dcm-plan-detail: ## デプロイ内容の差分を確認する（詳細）
	snow dcm plan --format json -c $(SNOWFLAKE_CLI_CONNECTION_NAME) --role $(DATACATALOG_OWNER_ROLE_NAME) | jq '.[0].result | fromjson'

.PHONY: dcm-deploy
dcm-deploy: ## DCM プロジェクトをデプロイする
	snow dcm deploy -c $(SNOWFLAKE_CLI_CONNECTION_NAME) --role $(DATACATALOG_OWNER_ROLE_NAME)

.PHONY: dcm-purge
dcm-purge: ## デプロイ済みのオブジェクトを削除する
	snow dcm purge --force -c $(SNOWFLAKE_CLI_CONNECTION_NAME) --role $(DATACATALOG_OWNER_ROLE_NAME)

.PHONY: dcm-drop
dcm-drop: ## DCM プロジェクトを削除する
	snow dcm drop -c $(SNOWFLAKE_CLI_CONNECTION_NAME) --role $(DATACATALOG_OWNER_ROLE_NAME)

.PHONY: manual-deploy-catalog
manual-deploy-catalog: ## DCM で管理できないオブジェクトをデプロイする
	snow sql -f manual/deploy/datacatalog/compute_pool.sql \
	  -D "datacatalog_compute_pool_name=$(DATACATALOG_COMPUTE_POOL_NAME)" \
	  -D "sis_owner_role_name=$(SIS_OWNER_ROLE_NAME)" \
	  -c $(SNOWFLAKE_CLI_CONNECTION_NAME) \
	  --role $(DATACATALOG_OWNER_ROLE_NAME)

.PHONY: manual-deploy-sample
manual-deploy-sample: ## DCM で管理できないオブジェクトをデプロイする（サンプルデータ向け）
	snow sql -f manual/deploy/sample/view.sql \
	  -D "datacatalog_database_name=$(DATACATALOG_DATABASE_NAME)" \
	  -c $(SNOWFLAKE_CLI_CONNECTION_NAME) \
	  --role $(DATACATALOG_OWNER_ROLE_NAME)

	snow sql -f manual/deploy/sample/contact.sql \
	  -D "datacatalog_database_name=$(DATACATALOG_DATABASE_NAME)" \
	  -D "SNOWFLAKE_MY_USER_NAME=$(SNOWFLAKE_MY_USER_NAME)" \
	  -c $(SNOWFLAKE_CLI_CONNECTION_NAME) \
	  --role $(DATACATALOG_OWNER_ROLE_NAME)

	snow sql -f manual/deploy/sample/masking.sql \
	  -D "datacatalog_database_name=$(DATACATALOG_DATABASE_NAME)" \
	  -D "datacatalog_owner_role_name=$(DATACATALOG_OWNER_ROLE_NAME)" \
	  -c $(SNOWFLAKE_CLI_CONNECTION_NAME) \
	  --role $(DATACATALOG_OWNER_ROLE_NAME)

	snow sql -f manual/deploy/sample/tag.sql \
	  -D "datacatalog_database_name=$(DATACATALOG_DATABASE_NAME)" \
	  -c $(SNOWFLAKE_CLI_CONNECTION_NAME) \
	  --role $(DATACATALOG_OWNER_ROLE_NAME)

.PHONY: manual-remove-catalog
manual-remove-catalog: ## 手動デプロイしたオブジェクトを削除する
	snow sql -f manual/remove/datacatalog/compute_pool.sql \
	  -D "datacatalog_compute_pool_name=$(DATACATALOG_COMPUTE_POOL_NAME)" \
	  -c $(SNOWFLAKE_CLI_CONNECTION_NAME) \
	  --role $(DATACATALOG_OWNER_ROLE_NAME)

.PHONY: manual-remove-sample
manual-remove-sample: ## 手動デプロイしたオブジェクトを削除する（サンプルデータ向け）
	snow sql -f manual/remove/sample/contact.sql \
	  -D "datacatalog_database_name=$(DATACATALOG_DATABASE_NAME)" \
	  -c $(SNOWFLAKE_CLI_CONNECTION_NAME) \
	  --role $(DATACATALOG_OWNER_ROLE_NAME)

	snow sql -f manual/remove/sample/masking.sql \
	  -D "datacatalog_database_name=$(DATACATALOG_DATABASE_NAME)" \
	  -c $(SNOWFLAKE_CLI_CONNECTION_NAME) \
	  --role $(DATACATALOG_OWNER_ROLE_NAME)
