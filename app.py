import streamlit as st
import sqlite3
import pandas as pd
import os

st.set_page_config(
    page_title="汽配 OE & 车型云端快查系统",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 专属访问密码
CORRECT_PASSWORD = "147258cc"

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 汽配数据快查系统 - 访问验证")
        pwd = st.text_input("请输入访问密码：", type="password")
        if st.button("登录"):
            if pwd == CORRECT_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ 密码错误，请重新输入")
        return False
    return True

if check_password():
    conn = sqlite3.connect("autoparts.db", check_same_thread=False)
    
    st.title("🚗 汽配 OE & 车型云端快查系统")
    st.caption("支持输入任意 OE 号 / 互换码 / 大厂码 / 适用车型 / SKU 进行模糊匹配")

    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(parts_table);")
    all_cols = [col[1] for col in cursor.fetchall()]
    searchable_cols = [c for c in all_cols if c != "图片路径"]

    with st.sidebar:
        st.header("📊 数据概览")
        total_count = pd.read_sql_query("SELECT COUNT(*) as cnt FROM parts_table", conn)["cnt"][0]
        st.write(f"收录零件总数: **{total_count}** 条")
        limit_num = st.slider("最大展示条数", min_value=10, max_value=200, value=50, step=10)
        
        if st.button("退出登录"):
            st.session_state["password_correct"] = False
            st.rerun()

    kw = st.text_input("🔍 搜索栏: ", placeholder="例如: K620054, Silverado, 515096 等")

    if kw.strip():
        conditions = " OR ".join([f"`{col}` LIKE ?" for col in searchable_cols])
        query = f"SELECT * FROM parts_table WHERE {conditions} LIMIT {limit_num}"
        params = [f"%{kw.strip()}%"] * len(searchable_cols)
        results = pd.read_sql_query(query, conn, params=params)

        st.success(f"为您匹配到 **{len(results)}** 条相关零件记录：")

        for idx, row in results.iterrows():
            with st.container():
                st.markdown("---")
                col_img, col_info = st.columns([1, 2])

                with col_img:
                    img_path = str(row.get("图片路径", "")).strip()
                    if img_path and os.path.exists(img_path):
                        st.image(img_path, use_container_width=True)
                    else:
                        st.info("暂无实物图片")

                with col_info:
                    for col in searchable_cols:
                        val = str(row[col]).strip()
                        if val and val != "None" and val != "nan":
                            st.markdown(f"**{col}:** {val}")