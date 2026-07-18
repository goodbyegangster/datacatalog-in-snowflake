# Technical Guidelines

Streamlit in Snowflake（SiS）実装規則を定義する。

## 実行環境 / 依存

- SiS container runtime を利用
- Python および各ライブラリーのバージョンは（[streamlit/pyproject.toml](../streamlit/pyproject.toml)）を参照
  - 依存関係は [streamlit/uv.lock](../streamlit/uv.lock) で管理
- Streamlit custom components は原則利用しない
  - SiS での動作制約があるため、グラフ等は組み込み機能で実装する

## Snowflake 接続

- セッション取得
  - SiS
    - `snowflake.snowpark.context.get_active_session()` を利用
  - ローカル開発
    - [.streamlit/secrets.toml](../streamlit/.streamlit/secrets.toml) を利用
  - 両対応の取得関数を 1 箇所に用意し、UI から直接接続処理を書かない
- SiS は `owner's rights` で動作する
  - アプリ閲覧者が誰であっても「アプリオーナーに見える範囲」を表示する
- 閲覧者情報が必要な場合は `st.user` を利用する

## データアクセス

- 本アプリで利用するデータは [streamlit/settings.py](../streamlit/settings.py) の `CATALOG_LOCATION` 記載のスキーマのみとなる
  - [docs/design-model.md](./design-model.md) 記載のカタログテーブルが、該当スキーマに所属する
    - カタログテーブルの生成は dcm ディレクトリの [procedure](../dcm/sources/definitions/procedure/) / [task](../dcm/sources/definitions/task/) が担う
  - そのため `SNOWFLAKE.ACCOUNT_USAGE` や対象データ本体には直接アクセスしない
- SQL / クエリは **data access モジュールに集約**し、UI 層（pages）は表示に専念する
- クエリ結果は `@st.cache_data(ttl=...)` でキャッシュする
  - TTL はマスター更新間隔（task は 3 時間ごと）に合わせ、長めに設定する（例：3600 秒程度）
- `CATALOG.ASSETS` / `COLUMNS` / `USERS` / `TAGS` はキャッシュして一括ロードし、検索 / フィルタは Python 側で行う方針を基本とする

## Directory Layout

- [streamlit/README.md](../streamlit/README.md) を参照
- 検索ロジックは `streamlit/logic/search/` 配下で責務別 package として管理する
  - `assets/filter.py`: データ資産検索条件の合成
  - `assets/freeword.py`: データ資産フリーワード検索
  - `assets/tags.py`: データ資産タグ検索
  - `users/filter.py`: ユーザー検索
  - `common/freeword.py`: フリーワード条件の解析
- Streamlit の UI 補助処理は `streamlit/components/common/` に置く
  - dataframe selection 取り出し、表示 formatter、badge 色定義など
- page をまたぐ runtime 契約は `streamlit/runtime/` に置く
  - `state.py`: `st.session_state` key 名
  - `navigation.py`: ページ間遷移 state と `st.switch_page()`
  - `widget_state.py`: ページをまたいで保持する検索 widget key
- page 共通の表示処理は `streamlit/views/common/` に置く
  - カタログロード時のエラー表示など

## 検索の実装

- ウィジェット：`st.text_input` / `st.checkbox` / `st.multiselect` / `st.segmented_control`（カテゴリー間の AND/OR）/ `st.expander`（カテゴリーのアコーディオン）
- 検索条件の合成やフリーワード解析は Streamlit から切り離した純関数として `logic/search` に置く
  - `logic.search` package の import は facade として利用してよい
  - 実処理は `__init__.py` ではなく責務別 module に置く
- 検索ウィジェットの選択値は `st.session_state` の key を明示して保持する。特にカテゴリー2（階層）の DB / スキーマ選択値は、[design-search.md](design-search.md) の連動仕様を成立させるため session_state 管理が必須:
  - スキーマの選択肢は、選択中の DB に**連動**して算出する（子プルダウンが親に依存）
  - DB プルダウンの `on_change` コールバックで、スキーマの選択 session_state をクリアし**未選択へリセット**する（未選択 = 無制約）
- ただし、`st.text_input(..., key=...)` など widget に紐づく session_state は widget の lifecycle に従う
  - 該当 widget が描画されないページへ遷移した場合、Streamlit の widget cleanup により値が消える可能性がある
  - 検索条件はページを離れても保持したいため、`streamlit_app.py` で検索 widget key を再代入し、Streamlit の widget cleanup を interrupt する
  - この横断ルールにより、graph ページから「データ資産に戻る」/「ユーザーに戻る」場合も検索結果一覧を維持する
- 「入力をクリア」は、ウィジェットキーを安定させたまま `session_state` へ初期値を明示代入して初期化する
  - `session_state` とフロント側ウィジェット値の同期に問題が出る場合のみ、キー世代（nonce）を進めてウィジェットを再生成する方式を fallback として検討する
- ログインユーザーのみ表示を適用する場合、`st.user` からユーザー名を取得できなければ fail-closed とする
  - 全ユーザー表示へ fallback せず、main pane に日本語メッセージを表示して一覧描画を止める
- SQL を動的に組む場合は**必ずパラメータバインディング**を使い、フリーワードを文字列連結しない（インジェクション防止）。識別子はクォート規約に従う

## テストコードの方針

現在の検討中の方針。production 側コードを testable なものにしておく。

- データアクセス / ロジック層
  - pytest を利用
  - フィルタ結合ロジック・「閲覧可能ユーザー」のロール階層展開を Streamlit から切り離した純関数にし、Snowflake 接続なしで検証可能とする
  - ローカルの画面確認 / AppTest では `CATALOG_DATA_MODE=fake` により fake catalog provider を利用する
  - Snowflake 接続処理は data access provider 側に閉じ込め、UI 層から直接呼ばない
- ページ / 状態層
  - `streamlit.testing.v1.AppTest` を利用
  - ブラウザ不要・CI 高速。検索ウィジェットの状態変化、検索結果、一覧表示、空状態 / エラー表示をカバー
  - ページをまたぐ検索 widget state 保持は、cleanup interrupt の対象 key を unit test で検証する
  - production 相当のエラーでは traceback を出さない。`CATALOG_DATA_MODE=fake` のローカル検証時のみ、原因調査のため `st.exception` を表示してよい
  - `st.dataframe` は pagination せず、`width="stretch"` と dataframe 側のスクロール / fullscreen 表示に委ねる
  - `st.dataframe` の selection が空の rerun は「詳細を閉じる」意思とは扱わず、既存の選択 state を維持する
  - `st.dataframe` の行選択や実際の詳細ペイン表示・タブ切替は AppTest が苦手なため、必要に応じて実ブラウザ確認へ回す
- e2e
  - PlayWright を利用
  - AppTest が苦手な部分だけ対応
  - 具体的には `st.dataframe` の行選択（`on_select`）、実レンダリング、実ブラウザのクリック / ナビゲーション
    - 数本のクリティカルフローに絞る
