#!/usr/bin/env bash
# .env の値から manifest.yml を生成する
set -Eeuo pipefail

readonly SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)
readonly DCM_DIR=$(dirname "$SCRIPT_DIR")
readonly REPO_ROOT=$(dirname "$DCM_DIR")

readonly ENV_FILE="${REPO_ROOT}/.env"
readonly TEMPLATE="${DCM_DIR}/manifest.yml.template"
readonly OUTPUT="${DCM_DIR}/manifest.yml"

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

# envsubst で置換する変数
# shellcheck disable=SC2016
readonly SUBST_VARS='
	$SNOWFLAKE_ACCOUNT_IDENTIFIER
	$DCM_DATABASE_NAME
	$DATACATALOG_DATABASE_NAME
	$DATACATALOG_OWNER_ROLE_NAME
	$SIS_OWNER_ROLE_NAME
	$SIS_READER_ROLE_NAME
	$DATACATALOG_WAREHOUSE_NAME
	$EXTERNAL_ACCESS_PYPI_NAME
'

# template ファイルから manifest.yml を生成する
envsubst "$SUBST_VARS" <"$TEMPLATE" >"$OUTPUT"

echo "Generated: ${OUTPUT}"
