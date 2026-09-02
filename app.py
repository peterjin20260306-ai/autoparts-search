import streamlit as st
import sqlite3
import pandas as pd
import os
import re

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
    st.caption("支持单件或【多件批量查询】（用空格、逗号、分号或换行隔开）")

    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(parts_table);")
    all_cols = [col[1] for col in cursor.fetchall()]
    searchable_cols = [c for c in all_cols if c != "图片路径"]

    with st.sidebar:
        st.header("📊 数据概览")
        total_count = pd.read_sql_query("SELECT COUNT(*) as cnt FROM parts_table", conn)["cnt"][0]
        st.write(f"收录零件总数: **{total_count}** 条")
        limit_num = st.slider("最大展示条数", min_value=10, max_value=500, value=100, step=10)
        
        if st.button("退出登录"):
            st.session_state["password_correct"] = False
            st.rerun()

    # 改为支持多行批量输入的多行文本框（Text Area）
    raw_input = st.text_area(
        "🔍 搜索栏 (支持一次性粘贴多个 OE 号、互换码、车型或 SKU):",
        placeholder="例如输入多个：\nK620054 515096\n或换行粘贴：\nK620054\n515096\nSilverado",
        height=100
    )

    if raw_input.strip():
        # 使用正则将空格、换行、中文/英文逗号、分号全部切分为关键词列表
        keywords = [k.strip() for k in re.split(r"[\s,;，；\n\r]+", raw_input) if k.strip()]
        
        if keywords:
            st.info(f"正在同时检索 **{len(keywords)}** 个关键词: `{'`、`'.join(keywords)}`")
            
            # 为每个关键词构建 OR 查询，再把多关键词组合起来
            outer_clauses = []
            params = []
            
            for kw in keywords:
                inner_clauses = [f"`{col}` LIKE ?" for col in searchable_cols]
                outer_clauses.append(f"({' OR '.join(inner_clauses)})")
                params.extend([f"%{kw}%"] * len(searchable_cols))
            
            # 多个关键词之间取并集（满足任一关键词即展示）
            where_sql = " OR ".join(outer_clauses)
            query = f"SELECT * FROM parts_table WHERE {where_sql} LIMIT {limit_num}"
            
            results = pd.read_sql_query(query, conn, params=params)

            st.success(f"共匹配到 **{len(results)}** 条相关零件记录：")

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