#!/usr/bin/env bash
#
# .env の値から .streamlit/secrets.toml を生成する。
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
readonly TEMPLATE="${STREAMLIT_DIR}/.streamlit/secrets.toml.template"
readonly OUTPUT="${STREAMLIT_DIR}/.streamlit/secrets.toml"

# envsubst で置換する変数を定義する。
# shellcheck disable=SC2016
readonly SUBST_VARS='
	$SNOWFLAKE_ACCOUNT_IDENTIFIER
	$SNOWFLAKE_MY_USER_NAME
	$SNOWFLAKE_MY_USER_PASSWORD
	$DATACATALOG_WAREHOUSE_NAME
	$DATACATALOG_DATABASE_NAME
'

# .env の値を使って .streamlit/secrets.toml を生成する。
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

	# 出力先ディレクトリを作成する。
	mkdir -p "$(dirname "$OUTPUT")"

	# 既存の secrets.toml を上書きして生成する。
	umask 077
	envsubst "$SUBST_VARS" <"$TEMPLATE" >"$OUTPUT"

	# secrets.toml の権限を所有者のみ読み書き可能に変更する。
	chmod 600 "$OUTPUT"

	echo "Generated: ${OUTPUT}"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
	main "$@"
fi
