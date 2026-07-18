# Refactor TODO

Streamlit in Snowflake アプリのリファクタリング候補を管理する。

前提:

- 対象は主に `streamlit/` 配下。
- `docs/` と実装に差異がある場合は、実装を正とする。
- SiS 制約を優先し、custom components や重い依存追加は避ける。
- 画面仕様・検索仕様を変えず、テストで守りながら小さく進める。

進捗記号: `[ ]` 未着手 / `[~]` 実装中 / `[x]` 完了 / `[?]` 要相談

## 優先度 高

- [x] ページ間遷移 state 操作を `runtime/navigation.py` へ集約する
  - 対象:
    - `streamlit/components/assets/detail/tab_users.py`
    - `streamlit/components/users/detail/pane.py`
    - `streamlit/views/graph.py`
  - 現状:
    - `NAV_TO_USER_NAME` / `NAV_TO_TABLE_ID` / `NAV_GRAPH_*` への代入と `st.switch_page()` が複数ファイルに散っている。
    - assets 起点 / users 起点の graph 遷移処理がほぼ同じ構造になっている。
  - 狙い:
    - 遷移先 page path、return_page、選択 state の積み方を 1 箇所で管理する。
    - ページ間遷移の仕様変更時に触る場所を減らす。
  - 注意:
    - `st.switch_page()` 自体は Streamlit 依存なので、純ロジック化ではなく runtime helper として扱う。

- [x] `st.dataframe` の single-cell selection 取り出し処理を共通化する
  - 対象:
    - `streamlit/components/assets/results.py`
    - `streamlit/components/users/results.py`
    - `streamlit/components/assets/detail/tab_users.py`
    - `streamlit/components/users/detail/pane.py`
  - 現状:
    - `event.selection.cells` の 1 行目を見て、表示 DataFrame の行位置へ戻す処理が重複している。
  - 狙い:
    - `components/dataframe_selection.py` のような小さい helper を作る。
    - AppTest が苦手な selection 周辺の仕様を 1 箇所に閉じ込める。
  - 注意:
    - selection が空の rerun では既存詳細を維持する、という設計は維持する。

- [x] ロール配列 / FQN / 表示文字列の formatter を共通化する
  - 対象:
    - `streamlit/components/assets/detail/tab_users.py`
    - `streamlit/components/users/detail/pane.py`
    - `streamlit/components/assets/detail/tab_columns.py`
  - 現状:
    - `_fmt_roles()` が重複している。
    - asset FQN の組み立てが複数箇所にある。
    - tags / foreign_keys / user_type などの表示整形が各 component に閉じている。
  - 狙い:
    - まずは完全に同じ `_fmt_roles()` と asset FQN だけを共通化する。
    - その後、必要に応じて `components/formatters.py` へ寄せる。
  - 注意:
    - 表示固有の細かい整形まで無理にまとめない。

- [x] カタログロード時のエラー表示を共通化する
  - 対象:
    - `streamlit/views/assets.py`
    - `streamlit/views/users.py`
    - `streamlit/views/graph.py`
  - 現状:
    - `try: catalog.load_*()`、日本語 `st.error()`、fake mode のみ `st.exception()` という処理が重複している。
  - 狙い:
    - `views/error_handling.py` または `runtime/errors.py` のような薄い helper に寄せる。
    - production では traceback を出さず、fake mode のみ出す規則を 1 箇所に置く。
  - 注意:
    - helper がデータロード関数まで隠しすぎると、各 page の読み込み対象が見えにくくなる。

## 優先度 中

- [x] assets/users page の「検索結果 + 詳細ペイン」制御を小さく整理する
  - 対象:
    - `streamlit/views/assets.py`
    - `streamlit/views/users.py`
  - 現状:
    - 検索 fingerprint、検索条件変更時の selection clear、一覧のみ / 左右分割 / 詳細維持の制御が page 内にまとまっている。
    - assets と users で似ているが、初期表示や nav 遷移時の挙動は異なる。
  - 狙い:
    - 共通化よりも、まず page 内の関数名と責務を揃える。
    - その後、必要なら「fingerprint 変更時に selection を clear する」程度の helper に留める。
  - 注意:
    - OOUI 的なページ単位の読みやすさを壊すほど抽象化しない。
  - 判断:
    - fingerprint 変更時の selection clear helper は、assets/users で呼び出し条件や clear 対象が異なるため共通化を見送る。

- [x] search component の state 初期化・clear・fingerprint を整理する
  - 対象:
    - `streamlit/components/assets/search.py`
    - `streamlit/components/users/search.py`
    - `streamlit/runtime/widget_state.py`
  - 現状:
    - `_defaults()`、`_init_state()`、`_clear()`、`fingerprint()` が各 search component にある。
    - widget cleanup interrupt 対象キーは `runtime/widget_state.py` にあるが、各 component の defaults と分離している。
  - 狙い:
    - 検索 widget key の定義漏れを防ぐ。
    - defaults と preserve 対象の関係を追いやすくする。
  - 注意:
    - Streamlit widget lifecycle の都合があるため、過度に汎用的な state manager は作らない。
  - 判断:
    - search component 側に `get_preserved_widget_keys()` を持たせ、`runtime/widget_state.py` は各 component の保持対象 key を合成するだけにした。
    - `_build_default_values()`、`_initialize_state()`、`_clear_search_inputs()`、`build_fingerprint()` へ命名を揃えた。
    - fingerprint は assets/users とも Value Object 化し、tuple の順番依存を避けた。

- [x] タグ検索 UI 用の tag metadata 生成を分離する
  - 対象:
    - `streamlit/components/assets/search.py`
  - 現状:
    - `_tag_allowed_values()` と `_tag_comment()` が、タグごとに `TAGS` DataFrame を走査している。
  - 狙い:
    - `SelectableTagKey` ごとの allowed values / comment を 1 回で組み立てる helper にする。
    - search UI の描画処理を短くする。
  - 注意:
    - 現状のデータ量では性能問題というより読みやすさの改善。
  - 判断:
    - `TagSearchMetadata` を追加し、タグ UI 描画に必要な `widget_key` / 選択肢 / コメントを事前に組み立てるようにした。
    - `render()` のタグ描画部分は metadata を順に描画し、検索条件へ変換するだけにした。

- [x] provider facade の型を `Protocol` で明確にする
  - 対象:
    - `streamlit/catalog/provider.py`
    - `streamlit/catalog/providers/fake.py`
    - `streamlit/catalog/providers/snowflake.py`
  - 現状:
    - `_provider()` は `ModuleType` を返し、各 `load_*()` 関数が存在する前提で呼んでいる。
  - 狙い:
    - fake / snowflake provider が満たすべき関数セットを型で表す。
    - 将来 provider を増やす場合の差し替え境界を明確にする。
  - 注意:
    - 実行時の仕組みは現状のままでよく、クラス化は必須ではない。
  - 判断:
    - `CatalogProvider` Protocol を追加し、provider module が満たすべき `load_*()` 関数セットを明示した。
    - `_provider()` の戻り値を `CatalogProvider` にし、fake / snowflake の切り替え方法は維持した。

- [x] Snowflake provider の normalize / JSON parse / scope filter をテストしやすくする
  - 対象:
    - `streamlit/catalog/providers/snowflake.py`
    - `streamlit/catalog/frame.py`
  - 現状:
    - `_normalize_catalog_table()`、`_parse_json_column()` は良い単位だが、Snowflake provider 内の private helper に閉じている。
    - `DISPLAY_SCOPES` 絞り込みは `catalog/frame.py` の `filter_rows_by_display_scopes()` へ切り出し済み。
  - 狙い:
    - 不正な列、VARIANT 由来 JSON、`DISPLAY_SCOPES` 絞り込みの unit test を追加しやすくする。
    - 将来データ形が揺れた時の防波堤にする。
  - 注意:
    - public API を増やしすぎず、テスト対象として private helper を許容するか、`catalog/frame.py` 等へ切り出すかを選ぶ。
  - 判断:
    - private helper はテスト対象にせず、`DISPLAY_SCOPES` 絞り込みだけを `catalog/frame.py` の public な純関数へ切り出した。
    - `filter_rows_by_display_scopes()` の unit test を追加し、DB / スキーマの一致条件を検証した。

- [ ] fake provider と tests fixture の重複を整理する
  - 対象:
    - `streamlit/catalog/providers/fake.py`
    - `streamlit/tests/fixtures/catalog_data.py`
  - 現状:
    - fake catalog と test fixture が似たデータを別々に持っている。
  - 狙い:
    - 画面確認用 fake data と unit test fixture のズレを減らす。
  - 注意:
    - test fixture はテスト意図を表すため、完全共通化しすぎない。

## 優先度 低 / 後続

- [ ] 実ブラウザ行選択の Playwright e2e を最小本数だけ追加する
  - 対象:
    - `streamlit/tests/e2e/` などを新設するか要検討。
  - 現状:
    - `docs/technical-guidelines.md` と `streamlit/todo.md` では、AppTest が苦手な `st.dataframe` 行選択は Playwright へ回す方針になっている。
  - 狙い:
    - データ資産選択 -> 詳細表示。
    - ユーザー選択 -> 詳細表示。
    - graph 遷移 -> 戻る。
  - 注意:
    - SiS ではなく fake mode のローカル Streamlit で確認する。

- [ ] `settings.py` 生成物と template の扱いを整理する
  - 対象:
    - `streamlit/settings.py`
    - `streamlit/settings.py.template`
    - `streamlit/scripts/init-settings-py.sh`
  - 現状:
    - 実行用の生成物が存在するため、template と実ファイルのどちらを見るべきかが初見で少し迷う。
  - 狙い:
    - README またはコメントで「生成物」「編集元」の関係を明確にする。
  - 注意:
    - これはコード整理というより運用整理。

- [ ] docs の追随差分を別タスクで整理する
  - 対象:
    - `docs/design-view.md`
    - `docs/design-search.md`
    - `docs/technical-guidelines.md`
  - 現状:
    - 実装が正。docs は設計意図の参照元だが、細部が実装に追随できていない可能性がある。
  - 狙い:
    - リファクタ後に、実装と違う説明があれば docs を更新する。
  - 注意:
    - 本 TODO では「docs に合わせて実装を戻す」判断はしない。

## 当面は見送る候補

- [?] assets/users page の完全共通 page framework 化
  - 理由:
    - 見た目の流れは似ているが、初期表示、ナビゲーション受け取り、詳細内容、検索条件の性質が違う。
    - 共通化しすぎると、OOUI 的なページ単位の読みやすさが落ちる可能性が高い。
  - 代替:
    - 重複している低レベル helper だけを先に切り出す。

- [?] search criteria / widget state の全面的な汎用 form 化
  - 理由:
    - Streamlit widget lifecycle と `session_state` cleanup interrupt の制約が強い。
    - 汎用化より、ページごとに明示的な key を持つ現在の設計のほうが安全。
  - 代替:
    - defaults / preserve keys の整合性チェックを追加する。

- [?] データアクセスの SQL pushdown
  - 理由:
    - 現行方針ではカタログ表を一括ロードし、検索 / フィルタは Python 側で行う。
    - 大規模化して転送量や初回表示が問題になるまでは、複雑さが増える。
  - 代替:
    - まずは provider の normalize / filtering 境界とテストを整える。

## 実施順の案

1. `runtime/navigation.py` を追加し、ページ間遷移 state 操作を集約する。
2. dataframe selection helper を追加し、4 箇所の selection 取り出しを置き換える。
3. `_fmt_roles()` と asset FQN formatter を共通化する。
4. カタログロード時のエラー表示 helper を追加する。
5. テストを実行し、必要に応じて AppTest / unit test を追加する。

各ステップは小さく分け、`uv run --group dev pytest` で確認する。
