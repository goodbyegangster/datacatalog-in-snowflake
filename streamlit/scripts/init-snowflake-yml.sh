#!/usr/bin/env bash
#
# .env の値から snowflake.yml を生成する。
#
# Requirement Bash Version
#   GNU Bash 4.4 or later
#
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd -P)"
readonly SCRIPT_DIR
STREAMLIT_DIR=$(dirname "$SCRIPT_DIR")
readonly STREAMLIT_DIR
REPO_ROOT=$(dirname "$STREAMLIT_DIR")
readonly REPO_ROOT

readonly ENV_FILE="${REPO_ROOT}/.env"
readonly TEMPLATE="${STREAMLIT_DIR}/snowflake.yml.template"
readonly OUTPUT="${STREAMLIT_DIR}/snowflake.yml"

# envsubst で置換する変数を定義する。
# shellcheck disable=SC2016
readonly SUBST_VARS='
	$DATACATALOG_DATABASE_NAME
	$STREAMLIT_TITLE_NAME
	$DATACATALOG_COMPUTE_POOL_NAME
	$DATACATALOG_WAREHOUSE_NAME
	$EXTERNAL_ACCESS_PYPI_NAME
'

# .env の値を使って snowflake.yml を生成する。
main() {
	if [[ ! -f "$ENV_FILE" ]]; then
		echo "Error: .env が見つかりません: ${ENV_FILE}" >&2
		echo "  cp .env.example .env で作成し、値を設定してください。" >&2
		exit 1
	fi

	if [[ ! -f "$TEMPLATE" ]]; then
		echo "Error: テンプレートが見つかりません: ${TEMPLATE}" >&2
		exit 1
	fi

	# .env を読み込んで環境変数として export する
	set -a
	source "$ENV_FILE"
	set +a

	# 既存の snowflake.yml を上書きして生成する。
	envsubst "$SUBST_VARS" <"$TEMPLATE" >"$OUTPUT"

	echo "Generated: ${OUTPUT}"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
	main "$@"
fi
