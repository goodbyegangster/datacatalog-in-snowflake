.DEFAULT_GOAL := help

include $(dir $(lastword $(MAKEFILE_LIST)))../.env

.PHONY: help
help:
	@printf "%-30s %-60s\n" "[Sub command]" "[Description]"
	@grep -hE '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "%-30s %-60s\n", $$1, $$2}'

.PHONY: setup
setup: ## DCM プロジェクト実行用のオブジェクトを作成する
	snow sql -f sql/setup.sql \
	  -D "SNOWFLAKE_MY_USER_NAME=$(SNOWFLAKE_MY_USER_NAME)" \
	  -D "dcm_project_owner_role_name=$(DCM_PROJECT_OWNER_ROLE_NAME)" \
	  -D "dcm_database_name=$(DCM_DATABASE_NAME)" \
	  -D "external_access_pypi_name=$(EXTERNAL_ACCESS_PYPI_NAME)" \
	  -c $(SNOWFLAKE_CLI_CONNECTION_NAME)

.PHONY: remove
remove: ## 作成済みオブジェクトを削除する
	snow sql -f sql/remove.sql \
	  -D "dcm_project_owner_role_name=$(DCM_PROJECT_OWNER_ROLE_NAME)" \
	  -D "dcm_database_name=$(DCM_DATABASE_NAME)" \
	  -D "external_access_pypi_name=$(EXTERNAL_ACCESS_PYPI_NAME)" \
	  -c $(SNOWFLAKE_CLI_CONNECTION_NAME)
