# todo-codex

## (1)

データ資産の詳細ペインを表示時、main pane の dataframe より「名前」列以外を hide column させることできるでしょうか。

main pane の幅が狭くなることで、すべての情報が美しく表示されないため、「名前」列のみの表示にしてしまいたい。

## (2)

データ資産詳細ペインの上半分のイメージ。

```python
with st.container(key="asset-summary"):
    st.subheader("CAMPAIGN_LEADS")
    st.caption("Marketing leads")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.caption("データベース")
        st.markdown(f"**hogehoge**")

    with col2:
        st.caption("スキーマ")
        st.markdown(f"**DATA_AD**")

    with col3:
        st.caption("オブジェクト種別")
        st.badge("VIEW", color="blue")

    with col4:
        st.caption("PUBLIC")
        st.badge("参照可能", color="pink")

    st.caption("タグ")
    st.markdown(
        ":blue-badge[:material/sell: DATA_DOMAIN] "
        ":gray-badge[MARKETING]"
    )
```

「オブジェクト種別」と「PUBLIC」は badge で表示させたい。オブジェクト種別は /home/kawata/work/datacatalog-in-snowflake/docs/design-model.md:182 に候補文字列があるから、表示カラーを定義したい。

タグも、同一 key は同一色の badge にしたい。表示タグは settings.py の指定により動的に変わるので、ここの表示カラーの定義をどのように管理すべきか検討したい。

## (3)

データ資産詳細ペインの「閉じる」ボタンは右上に配置したい。且つ、primaryColor を利用したい。

## (4)

データ資産詳細ペインの contact tab の表示を dataframe としたい。表示に一貫性を持たせたい。結局、dataframe は便利な機能が多い。

## (5)

データ資産詳細ペインの stats tab の表示を dataframe としたい。表示に一貫性を持たせたい。結局、dataframe は便利な機能が多い。

## (6)

データ資産詳細ペインの column tab の表示も dataframe としたい。表示に一貫性を持たせたい。dataframe にするのであれば、ORDINAL_POSITION も表示したい。

結局、dataframe は便利な機能が多い。ただし、TAGS が配列なので、どのように表示するのが適当か検討したい。
