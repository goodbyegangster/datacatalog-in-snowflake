# ruff: noqa: S101

from __future__ import annotations

from catalog import schema
from lib import search
from lib.search import AssetSearchCriteria, FreewordQuery, TagSelection, UserFreewordQuery
from tests.fixtures import catalog_data


def asset_names(df):
    return df[schema.Assets.ASSET_NAME].tolist()


def user_names(df):
    return df[schema.Users.USER_NAME].tolist()


def tag_selection(tag_name: str, selected: list[str]) -> TagSelection:
    return TagSelection(
        tag_database=catalog_data.DB,
        tag_schema=catalog_data.TAG_SCHEMA,
        tag_name=tag_name,
        selected=selected,
        allowed=selected,
    )


def test_parse_freeword_uses_or_before_and() -> None:
    assert search.parse_freeword("orders OR leads AND customer") == (
        "or",
        ["orders", "leads AND customer"],
    )
    assert search.parse_freeword("orders AND amount") == ("and", ["orders", "amount"])
    assert search.parse_freeword("  ") == ("and", [])


def test_filter_assets_matches_column_freeword() -> None:
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
    criteria = AssetSearchCriteria(
        selected_databases=[catalog_data.DB],
        selected_schemas=["DATA_SALES"],
        selected_types=["BASE TABLE"],
    )

    result = search.filter_assets(catalog_data.assets(), catalog_data.columns(), criteria)

    assert asset_names(result) == ["ORDERS"]


def test_filter_assets_applies_category_or_bucket() -> None:
    criteria = AssetSearchCriteria(
        selected_schemas=["DATA_AD"],
        selected_types=["DYNAMIC TABLE"],
        hierarchy_or=True,
        type_or=True,
    )

    result = search.filter_assets(catalog_data.assets(), catalog_data.columns(), criteria)

    assert asset_names(result) == ["CAMPAIGN_LEADS", "CUSTOMERS"]


def test_filter_assets_matches_tags_on_asset_and_columns() -> None:
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


def test_scope_options_come_from_display_scopes(monkeypatch) -> None:
    monkeypatch.setattr(
        search,
        "DISPLAY_SCOPES",
        [
            {"DATABASE_NAME": "DB1", "SCHEMA_NAME": "S1"},
            {"DATABASE_NAME": "DB1", "SCHEMA_NAME": "S2"},
            {"DATABASE_NAME": "DB2", "SCHEMA_NAME": "S3"},
        ],
    )

    assert search.scope_databases() == ["DB1", "DB2"]
    assert search.scope_schemas(["DB1"]) == ["S1", "S2"]


def test_filter_users_matches_freeword_and_self_filter() -> None:
    users = catalog_data.users()

    only_self = search.filter_users(users, UserFreewordQuery(), only_user_name="ALICE")
    service = search.filter_users(users, UserFreewordQuery(text="service"))
    alice_and_analytics = search.filter_users(users, UserFreewordQuery(text="alice AND analytics"))

    assert user_names(only_self) == ["ALICE"]
    assert user_names(service) == ["SVC_ETL"]
    assert user_names(alice_and_analytics) == ["ALICE"]
