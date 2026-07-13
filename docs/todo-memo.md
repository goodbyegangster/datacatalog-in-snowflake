# todo-memo

## Snowflake ロールを分離

以下の責務で Snowflake ロールを分離する。

- dcm object owner / 実行ロール
- datacatalog owner
- sis app owner
- sis app reader

## サンプルオブジェクト用の専用データベースを用意

datacatalog 向けとサンプルデータ向けを、データベース単位で分ける。

## サンプルオブジェクト追加

dynamic table を追加。

## Snowflake タスクの実行ロール

ACCOUNTADMIN で実行ができるようにする。

## フリーワード検索

全てのチェックボックスを外した場合、入力不可にする。

## assets のタグのカラー配色

- タグの文字数に依存したロジックでは、容易に同一色が生まれてしまう
  - 色のパターン数を増やして、配色ロジックを変えたい

## 既に detail 表示時に、table の fullscreen より行を選択した際、選択行のdetailまで画面遷移しない件

- assets および users のどちらでも、この動作になる
- 画面遷移させたい

## assets の カラムタブの列ヘッダー位置

以下の列ヘッダーを「中央より」にする。

- PKEY
- NOT NULL
- UNIQUE
- マスキングポリシー => masking policy に値を変更

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
