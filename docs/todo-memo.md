# todo-memo

## Snowflake ロールを分離

以下の責務で Snowflake ロールを分離する。

- dcm object owner / 実行ロール
- datacatalog owner
- sis app owner
- sis app reader

## サンプルオブジェクト用の専用データベースを用意

datacatalog 向けとサンプルデータ向けを、データベース単位で分ける。
=> これは sample であることが分かるスキーマ名にすれば良し。データベース単位ではわけない。

## サンプルオブジェクト追加

dynamic table を追加。

## Snowflake タスクの実行ロール

ACCOUNTADMIN で実行ができるようにする。

- タスク実行ロールに `grant manage grants on account to role <% dcm_project_owner_role_name %>` を付与すればOK

## 既に detail 表示時に、table の fullscreen より行を選択した際、選択行のdetailまで画面遷移しない件

- assets および users のどちらでも、この動作になる
- 画面遷移させたい

## assets の ユーザータブの「ユーザー付与ロール」と「データ資産付与ロール」

アルファベット順に表示するように。

## users の ユーザータブの「ユーザー付与ロール」と「データ資産付与ロール」

アルファベット順に表示するように。

## ロール継承グラフ

- legend を追加
- 「戻る」ボタンを配置？
  - 検索の一覧結果を state で持たせれば、「戻る」の動作が実現できるか

## 実行環境

| | 実行環境 | Snowflake 接続 |
| --- | --- | --- |
| 1 | Snowflake Container Runtime | あり |
| 2 | ローカル | あり |
| 3 | ローカル | なし |

### 改善点

- assets の search で、database / schema が DISPLAY_SCOPES 依存のため、Fake で動作が変になる

## search.py のリファクタリング

[search.py](/home/kawata/educ/datacatalog-in-snowflake/streamlit/logic/search.py) を表示ページ毎に整理できないか。
