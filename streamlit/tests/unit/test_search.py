# ruff: noqa: S101

from __future__ import annotations

import pandas as pd

from catalog import schema
from logic import search
from logic.search import AssetSearchCriteria, FreewordQuery, TagSelection, UserFreewordQuery
from tests.fixtures import catalog_data


def asset_names(df: pd.DataFrame) -> list[str]:
    """データ資産名をリストで返す。"""
    return df[schema.Assets.ASSET_NAME].tolist()


def user_names(df: pd.DataFrame) -> list[str]:
    """ユーザー名をリストで返す。"""
    return df[schema.Users.USER_NAME].tolist()


def tag_selection(tag_name: str, selected: list[str]) -> TagSelection:
    """テスト用のタグ選択条件を返す。"""
    return TagSelection(
        tag_database=catalog_data.database_name(),
        tag_schema=catalog_data.tag_schema_name(tag_name),
        tag_name=tag_name,
        selected=selected,
        tag_value_options=selected,
    )


def test_parse_freeword_uses_or_before_and() -> None:
    """OR を AND より先に分割する。"""
    assert search.parse_freeword("orders OR leads AND customer") == (
        "or",
        ["orders", "leads AND customer"],
    )
    assert search.parse_freeword("orders AND amount") == ("and", ["orders", "amount"])
    assert search.parse_freeword("  ") == ("and", [])


def test_filter_assets_matches_column_freeword() -> None:
    """カラムのフリーワード一致で資産を返す。"""
    criteria = AssetSearchCriteria(
        freeword=FreewordQuery(
            text="email",
            target_asset_name=False,
            target_asset_desc=False,
            target_column_name=True,
            target_column_desc=False,
        )
    )

    result = search.filter_assets(catalog_data.assets(), catalog_data.columns(), criteria)

    assert asset_names(result) == ["CAMPAIGN_LEADS", "CUSTOMERS"]


def test_filter_assets_matches_and_and_or_freeword() -> None:
    """AND と OR のフリーワード検索を適用する。"""
    assets = catalog_data.assets()
    columns = catalog_data.columns()

    and_result = search.filter_assets(
        assets,
        columns,
        AssetSearchCriteria(freeword=FreewordQuery(text="Customer AND master")),
    )
    or_result = search.filter_assets(
        assets,
        columns,
        AssetSearchCriteria(freeword=FreewordQuery(text="orders OR campaign")),
    )

    assert asset_names(and_result) == ["CUSTOMERS"]
    assert asset_names(or_result) == ["ORDERS", "CAMPAIGN_LEADS"]


def test_filter_assets_applies_hierarchy_and_type_as_and_bucket() -> None:
    """階層と種別を AND 条件として適用する。"""
    criteria = AssetSearchCriteria(
        selected_databases=[catalog_data.database_name()],
        selected_schemas=["DATA_SALES"],
        selected_types=["BASE TABLE"],
    )

    result = search.filter_assets(catalog_data.assets(), catalog_data.columns(), criteria)

    assert asset_names(result) == ["ORDERS"]


def test_filter_assets_applies_category_or_bucket() -> None:
    """カテゴリ条件を OR bucket として適用する。"""
    criteria = AssetSearchCriteria(
        selected_schemas=["DATA_AD"],
        selected_types=["DYNAMIC TABLE"],
        is_hierarchy_or_enabled=True,
        is_type_or_enabled=True,
    )

    result = search.filter_assets(catalog_data.assets(), catalog_data.columns(), criteria)

    assert asset_names(result) == ["CAMPAIGN_LEADS", "CUSTOMERS"]


def test_filter_assets_matches_tags_on_asset_and_columns() -> None:
    """資産タグとカラムタグの両方で検索する。"""
    assets = catalog_data.assets()
    columns = catalog_data.columns()

    asset_tag_result = search.filter_assets(
        assets,
        columns,
        AssetSearchCriteria(tag_selections=[tag_selection("DATA_DOMAIN", ["SALES"])]),
    )
    column_tag_result = search.filter_assets(
        assets,
        columns,
        AssetSearchCriteria(tag_selections=[tag_selection("PII", ["YES"])]),
    )
    multi_tag_result = search.filter_assets(
        assets,
        columns,
        AssetSearchCriteria(
            tag_selections=[
                tag_selection("DATA_DOMAIN", ["SALES"]),
                tag_selection("SENSITIVITY", ["CONFIDENTIAL"]),
            ]
        ),
    )

    assert asset_names(asset_tag_result) == ["ORDERS"]
    assert asset_names(column_tag_result) == ["CAMPAIGN_LEADS", "CUSTOMERS"]
    assert asset_names(multi_tag_result) == ["ORDERS"]


def test_freeword_match_reasons_show_asset_and_column_hits() -> None:
    """一致理由に資産とカラムのヒット箇所を表示する。"""
    reasons = search.freeword_match_reasons(
        FreewordQuery(text="email"),
        catalog_data.assets(),
        catalog_data.columns(),
    )

    assert reasons[2].text == "カラム名 EMAIL、カラム説明 EMAIL に一致。"
    assert reasons[3].text == "カラム名 CUSTOMER_EMAIL、カラム説明 CUSTOMER_EMAIL に一致。"


def test_freeword_match_reasons_split_object_and_column_sentences() -> None:
    """オブジェクトとカラムの一致理由を文で分ける。"""
    reasons = search.freeword_match_reasons(
        FreewordQuery(text="order"),
        catalog_data.assets(),
        catalog_data.columns(),
    )

    assert (
        reasons[1].text
        == "名前 / 説明 に一致。カラム名 ORDER_ID、カラム説明 ORDER_ID, AMOUNT に一致。"
    )


def test_freeword_match_reasons_limit_column_names() -> None:
    """一致理由に表示するカラム名を上限で省略する。"""
    columns_schema = schema.Columns
    columns = catalog_data.columns()
    extra_columns = pd.DataFrame(
        [
            {
                **columns.iloc[0].to_dict(),
                columns_schema.COLUMN_NAME: "ORDER_EMAIL",
                columns_schema.ORDINAL_POSITION: 3,
                columns_schema.DESCRIPTION: "Order email",
            },
            {
                **columns.iloc[0].to_dict(),
                columns_schema.COLUMN_NAME: "BILLING_EMAIL",
                columns_schema.ORDINAL_POSITION: 4,
                columns_schema.DESCRIPTION: "Billing email",
            },
            {
                **columns.iloc[0].to_dict(),
                columns_schema.COLUMN_NAME: "SHIPPING_EMAIL",
                columns_schema.ORDINAL_POSITION: 5,
                columns_schema.DESCRIPTION: "Shipping email",
            },
        ]
    )
    columns = pd.concat([columns, extra_columns], ignore_index=True)

    reasons = search.freeword_match_reasons(
        FreewordQuery(
            text="email",
            target_asset_name=False,
            target_asset_desc=False,
            target_column_name=True,
            target_column_desc=False,
        ),
        catalog_data.assets(),
        columns,
    )

    assert reasons[1].text == "カラム名 ORDER_EMAIL, BILLING_EMAIL ほか1件 に一致。"


def test_scope_options_come_from_assets() -> None:
    """スコープ候補を資産一覧から生成する。"""
    assets_schema = schema.Assets
    assets = pd.DataFrame(
        [
            {assets_schema.DATABASE_NAME: "DB2", assets_schema.SCHEMA_NAME: "S3"},
            {assets_schema.DATABASE_NAME: "DB1", assets_schema.SCHEMA_NAME: "S2"},
            {assets_schema.DATABASE_NAME: "DB1", assets_schema.SCHEMA_NAME: "S1"},
            {assets_schema.DATABASE_NAME: "DB1", assets_schema.SCHEMA_NAME: "S1"},
        ]
    )

    assert search.get_scope_database_names(assets) == ["DB1", "DB2"]
    assert search.get_scope_schema_names(assets, ["DB1"]) == ["S1", "S2"]
    assert search.get_scope_schema_names(assets, []) == []


def test_filter_users_matches_freeword_and_self_filter() -> None:
    """ユーザーのフリーワードと自ユーザー絞り込みを適用する。"""
    users = catalog_data.users()

    only_self = search.filter_users(
        users,
        UserFreewordQuery(),
        current_user_filter_name="ALICE",
    )
    service = search.filter_users(users, UserFreewordQuery(freeword_text="service"))
    alice_and_analytics = search.filter_users(
        users,
        UserFreewordQuery(freeword_text="alice AND analytics"),
    )

    assert user_names(only_self) == ["ALICE"]
    assert user_names(service) == ["SVC_ETL"]
    assert user_names(alice_and_analytics) == ["ALICE"]
