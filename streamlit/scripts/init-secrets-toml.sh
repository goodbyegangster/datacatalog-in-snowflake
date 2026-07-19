#!/usr/bin/env bash
# .env の値から .streamlit/secrets.toml を生成する。
set -Eeuo pipefail

readonly SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)
readonly STREAMLIT_DIR=$(dirname "$SCRIPT_DIR")
readonly REPO_ROOT=$(dirname "$STREAMLIT_DIR")

readonly ENV_FILE="${REPO_ROOT}/.env"
readonly TEMPLATE="${STREAMLIT_DIR}/.streamlit/secrets.toml.template"
readonly OUTPUT="${STREAMLIT_DIR}/.streamlit/secrets.toml"

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

# 出力先ディレクトリを用意する
mkdir -p "$(dirname "$OUTPUT")"

# envsubst で置換する変数
# shellcheck disable=SC2016
readonly SUBST_VARS='
	$SNOWFLAKE_ACCOUNT_IDENTIFIER
	$SNOWFLAKE_MY_USER_NAME
	$SNOWFLAKE_MY_USER_PASSWORD
	$DATACATALOG_WAREHOUSE_NAME
	$DATACATALOG_DATABASE_NAME
'

# template ファイルから secrets.toml を生成する
umask 077
envsubst "$SUBST_VARS" <"$TEMPLATE" >"$OUTPUT"
chmod 600 "$OUTPUT"

echo "Generated: ${OUTPUT}"
