.DEFAULT_GOAL := help

include $(dir $(lastword $(MAKEFILE_LIST)))../.env

.PHONY: help
help:
	@printf "%-30s %-60s\n" "[Sub command]" "[Description]"
	@grep -hE '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "%-30s %-60s\n", $$1, $$2}'

.PHONY: update-snowflake-schema-json
update-snowflake-schema-json: ## .config/snowflake-schema.json を最新化する
	snow helpers generate-project-schema > .config/snowflake-schema.json

.PHONY: init-snowflake-yml
init-snowflake-yml: ## .env から snowflake.yml を生成する
	bash ./scripts/init-snowflake-yml.sh

.PHONY: init-secrets-toml
init-secrets-toml: ## .env から .streamlit/secrets.toml を生成する
	bash ./scripts/init-secrets-toml.sh

.PHONY: init-settings-py
init-settings-py: ## .env から settings.py を生成する
	bash ./scripts/init-settings-py.sh

.PHONY: run_local
run_local: ## ローカルサーバーを起動
	streamlit run streamlit_app.py

.PHONY: deploy
deploy: ## Snowflake へデプロイ
	snow streamlit deploy --replace \
	  -c $(SNOWFLAKE_CLI_CONNECTION_NAME) \
	  --role $(SIS_ROLE_PREFIX)_FUNC_SIS_OWNER
