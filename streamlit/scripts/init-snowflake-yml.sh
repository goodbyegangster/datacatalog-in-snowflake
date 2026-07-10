#!/usr/bin/env bash
# shellcheck disable=SC2155
#
# .env の値から snowflake.yml を生成する。
set -Eeuo pipefail

readonly SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)
readonly STREAMLIT_DIR=$(dirname "$SCRIPT_DIR")
readonly REPO_ROOT=$(dirname "$STREAMLIT_DIR")

readonly ENV_FILE="${REPO_ROOT}/.env"
readonly TEMPLATE="${STREAMLIT_DIR}/snowflake.yml.template"
readonly OUTPUT="${STREAMLIT_DIR}/snowflake.yml"

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
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

# envsubst で置換する変数
# shellcheck disable=SC2016
readonly SUBST_VARS='
  $SIS_DATABASE_NAME
  $STREAMLIT_TITLE_NAME
  $SIS_COMPUTE_POOL_NAME
  $SIS_WAREHOUSE_NAME
  $EXTERNAL_ACCESS_PYPI_NAME
'

# template ファイルから snowflake.yml を生成する
envsubst "$SUBST_VARS" <"$TEMPLATE" >"$OUTPUT"

echo "Generated: ${OUTPUT}"
