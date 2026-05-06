import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 기본 설정 (와이드 모드)
st.set_page_config(page_title="서울시 따릉이 대시보드", layout="wide")

# 2. 데이터베이스 연결 확인 및 함수 정의
DB_PATH = 'bicycle.db'

def check_db():
    """DB 파일 존재 여부 확인"""
    if not os.path.exists(DB_PATH):
        st.error(f"🚨 에러: '{DB_PATH}' 파일을 찾을 수 없습니다. 파일이 app.py와 같은 폴더에 있는지 확인해주세요.")
        st.stop()

@st.cache_data
def run_query(query):
    """SQL 쿼리를 실행하여 판다스 데이터프레임으로 반환 (캐싱 기능 포함)"""
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql(query, conn)

# 실행 전 DB 체크
check_db()

# 대시보드 제목
st.title("🚲 서울시 따릉이 공공데이터 분석 대시보드")
st.markdown("공공데이터를 활용하여 따릉이 이용 패턴 및 운영 전략을 분석합니다.")
st.divider()

# ---------------------------------------------------------
# [차트 1] 연령대별 이용건수 + 정기권 이용건수 (콤보차트)
# ---------------------------------------------------------
st.header("1. 연령대별 이용 패턴 (전체 vs 정기권)")

col1_1, col1_2 = st.columns([2, 1]) # 좌측 차트, 우측 설명

with col1_1:
    sql1 = """
    SELECT 연령대코드, 
           SUM(이용건수) as 총이용건수,
           SUM(CASE WHEN 대여구분코드 = '정기권' THEN 이용건수 ELSE 0 END) as 정기권이용건수
    FROM 이용정보
    GROUP BY 연령대코드
    ORDER BY 연령대코드
    """
    df1 = run_query(sql1)

    # Plotly 콤보 차트 생성
    fig1 = go.Figure()
    # 막대 그래프 (총 이용건수)
    fig1.add_trace(go.Bar(x=df1['연령대코드'], y=df1['총이용건수'], name='총 이용건수', marker_color='skyblue'))
    # 라인 그래프 (정기권 이용건수)
    fig1.add_trace(go.Scatter(x=df1['연령대코드'], y=df1['정기권이용건수'], name='정기권 이용건수', mode='lines+markers', line=dict(color='orange', width=3)))

    fig1.update_layout(title="연령대별 이용 현황", xaxis_title="연령대", yaxis_title="건수", hovermode="x unified")
    st.plotly_chart(fig1, use_container_width=True)

with col1_2:
    st.subheader("🔍 SQL Query")
    st.code(sql1, language='sql')
    st.subheader("💡 인사이트")
    st.write("- 2030 세대의 이용량이 압도적으로 높음을 알 수 있습니다.")
    st.write("- 정기권 이용 비중을 통해 주력 이용층의 충성도를 파악할 수 있습니다.")

st.divider()

# ---------------------------------------------------------
# [차트 2] 대여소 QR/LCD + 이용건수 지도 시각화
# ---------------------------------------------------------
st.header("2. 대여소 위치 및 운영 방식별 이용량")

col2_1, col2_2 = st.columns([2, 1])

with col2_1:
    sql2 = """
    SELECT s.보관소명, s.위도, s.경도, s.운영방식,
           SUM(i.이용건수) as 총이용건수
    FROM 대여소 s
    JOIN 이용정보 i ON s.대여소번호 = i.대여소번호
    GROUP BY s.대여소번호
    """
    df2 = run_query(sql2)

    # 지도 시각화 (Plotly Scatter Mapbox)
    fig2 = px.scatter_mapbox(df2, 
                             lat="위도", lon="경도", 
                             size="총이용건수", 
                             color="운영방식",
                             hover_name="보관소명",
                             color_discrete_map={'QR': 'red', 'LCD': 'blue', '운영방식미설정': 'gray'},
                             zoom=10, height=500)
    fig2.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig2, use_container_width=True)

with col2_2:
    st.subheader("🔍 SQL Query")
    st.code(sql2, language='sql')
    st.subheader("💡 인사이트")
    st.write("- **빨간색(QR)**과 **파란색(LCD)**으로 대여소의 하드웨어 구분을 할 수 있습니다.")
    st.write("- 원의 크기가 클수록 이용건수가 많은 '핫플레이스' 대여소입니다.")

st.divider()

# ---------------------------------------------------------
# [차트 3] 기온 구간별 평균 이용시간 (막대그래프)
# ---------------------------------------------------------
st.header("3. 기온 변화에 따른 평균 이용 시간 분석")

col3_1, col3_2 = st.columns([2, 1])

with col3_1:
    sql3 = """
    SELECT 
        CASE 
            WHEN t.평균기온 < 10 THEN '① 저온 (10도 미만)'
            WHEN t.평균기온 BETWEEN 10 AND 25 THEN '② 적정 (10~25도)'
            ELSE '③ 고온 (25도 이상)'
        END as 기온구간,
        AVG(i.이용시간) as 평균이용시간
    FROM 이용정보 i
    JOIN 기온 t ON i.대여일자 = t.년월
    GROUP BY 기온구간
    ORDER BY 기온구간
    """
    df3 = run_query(sql3)

    fig3 = px.bar(df3, x='기온구간', y='평균이용시간', 
                  color='기온구간', text_auto='.1f',
                  title="기온 구간별 평균 이용시간 (분)")
    st.plotly_chart(fig3, use_container_width=True)

with col3_2:
    st.subheader("🔍 SQL Query")
    st.code(sql3, language='sql')
    st.subheader("💡 인사이트")
    st.write("- 기온이 **적정(10~25도)** 수준일 때 이용 시간이 가장 길게 나타나는 경향이 있습니다.")
    st.write("- 너무 춥거나 더운 날씨에는 이동 목적 위주의 짧은 이용이 많음을 시사합니다.")

st.sidebar.info("데이터 출처: 서울특별시 공공데이터 포털")