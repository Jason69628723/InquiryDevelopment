import streamlit as st
import pandas as pd

# 主分類&簡化對照
main_categories = [
    "Auxiliary Equipment and Integrated",
    "Blow Molding Machines",
    "Plastic Converting Machines",
    "Extruders and Extrusion Lines",
    "Finished/Semi-finished Product/OEM/ODM",
    "Injection Molding Machines",
    "Molds and Dies",
    "other",
    "Packaging Machinery",
    "Parts and Components",
    "Printing Machinery",
    "Raw Materials & Additives",
    "Plastic Recycling & Material Process",
    "Rubber Processing Machinery",
    "Shoe Making Machinery",
    "Thermoforming Machines"
]
maincat_map = {
    "Auxiliary Equipment and Integrated": "Auxiliary",
    "Blow Molding Machines": "Blow",
    "Plastic Converting Machines": "Converting",
    "Extruders and Extrusion Lines": "Extruders",
    "Finished/Semi-finished Product/OEM/ODM": "Finished",
    "Injection Molding Machines": "Injection",
    "Molds and Dies": "Molds",
    "other": "Other",
    "Packaging Machinery": "Packaging",
    "Parts and Components": "Parts",
    "Printing Machinery": "Printing",
    "Raw Materials & Additives": "Raw",
    "Plastic Recycling & Material Process": "Recycling",
    "Rubber Processing Machinery": "Rubber",
    "Shoe Making Machinery": "Shoe",
    "Thermoforming Machines": "Thermoforming"
}
manual_country_map = {
    'United Arab Emirates': 'Asia',
    'United Kingdom': 'Europe',
    'United States': 'North America',
    'Turkiye': 'Asia',
    'Chad': 'C/S America'
}

st.title("Inquiry Development 自動化小工具")

# 上傳詢問函&國家對照表
csv_file = st.file_uploader("請上傳詢問函CSV檔（必填）", type="csv")
country_file = st.file_uploader("請上傳國家對照表（CSV，必填）", type="csv")

if csv_file and country_file:
    df = pd.read_csv(csv_file)
    country_map = pd.read_csv(country_file)
    country_map.columns = [col.strip() for col in country_map.columns]

    st.subheader("第一步：詢問函分類統計")
    # 統計無效/有效分類
    spam_count = df['Status'].str.contains('spam', case=False, na=False).sum()
    repeated_count = df['Status'].str.contains('repeated', case=False, na=False).sum()
    no_dev_count = (df['Status'] == '不用開發').sum()
    pass_sales_count = df['Status'].str.contains('pass給業務', na=False).sum()
    offline_count = df['Remarks'].fillna('').str.contains('offline', case=False).sum()
    valid_count = df['Status'].isin(['國貿開發', '指定選客戶']).sum()
    trade_dev_count = (df['Status'] == '國貿開發').sum()
    assigned_cust_count = (df['Status'] == '指定選客戶').sum()
    invalid_total = no_dev_count + spam_count + repeated_count
    invalid_ratio = (invalid_total / (invalid_total + valid_count) * 100) if (invalid_total + valid_count) else 0

    st.write(f"無效詢問函總數: {invalid_total}")
    st.write(f"  - 不用開發: {no_dev_count}")
    st.write(f"  - SPAM: {spam_count}")
    st.write(f"  - REPEATED: {repeated_count}")
    st.write(f"  - Pass給業務: {pass_sales_count}")
    st.write(f"  - Offline: {offline_count}")
    st.write(f"有效詢問函總數: {valid_count}（國貿開發:{trade_dev_count}；指定選客戶:{assigned_cust_count}）")
    st.write(f"無效詢問函比例: {invalid_ratio:.1f}%")

    # 防呆檢查
    st.subheader("第二步：必填欄位檢查")
    must_have = ['大分類/Main Category', '詢問函國家/Inquiry Country']
    missing_rows = df[df['Status'].isin(['國貿開發', '指定選客戶'])][must_have].isnull().any(axis=1)
    if missing_rows.sum() > 0:
        st.error("有以下有效詢問函缺少必填欄位，請補齊後再繼續：")
        st.dataframe(df[df['Status'].isin(['國貿開發', '指定選客戶'])][missing_rows])
        st.stop()
    else:
        st.success("所有有效詢問函必填欄位都已齊全，繼續處理！")

    st.subheader("第三步：分類拆分與報表下載")
    all_valid = df[df['Status'].isin(['國貿開發', '指定選客戶'])]
    final_rows = []
    for _, row in all_valid.iterrows():
        maincat_text = str(row['大分類/Main Category'])
        found_cats = [cat for cat in main_categories if cat in maincat_text]
        if len(found_cats) > 1:
            for cat in found_cats:
                final_rows.append({
                    'Status': row['Status'],
                    'Main Category': cat,
                    'Country': row['詢問函國家/Inquiry Country']
                })
        else:
            cat = found_cats[0] if found_cats else row['大分類/Main Category']
            final_rows.append({
                'Status': row['Status'],
                'Main Category': cat,
                'Country': row['詢問函國家/Inquiry Country']
            })
    result_df = pd.DataFrame(final_rows)
    result_df['category'] = result_df['Main Category'].map(maincat_map).fillna('Other')
    result_df['Country Clean'] = result_df['Country'].str.strip()
    result_df = result_df.merge(country_map, left_on='Country Clean', right_on=country_map.columns[0], how='left')
    for k, v in manual_country_map.items():
        result_df.loc[result_df['Country Clean'] == k, country_map.columns[1]] = v
    result_df['continent'] = result_df[country_map.columns[1]]
    final_excel = result_df[['Status', 'Main Category', 'Country Clean', 'continent', 'category']]
    final_excel.columns = ['Status', 'Main Category', 'Country', 'continent', 'category']

    st.write(f"本次共計 **{final_excel.shape[0]}** 封 category inquiry")
    st.dataframe(final_excel.head(10))
    # 下載
    st.download_button("下載完整Excel報表", data=final_excel.to_csv(index=False).encode('utf-8-sig'),
                       file_name='inquiry_development_result.csv', mime='text/csv')
