import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io

# ==========================================
# 1. K-PROTOCOL Universal Constants
# ==========================================
C_K = 297880197.6
R_EARTH = 6371000.0
G_STD = 9.80665
PI_SQ = np.pi ** 2

# ==========================================
# 2. Page Configuration & Custom CSS
# ==========================================
st.set_page_config(page_title="K-PROTOCOL 6G Omni Center", layout="wide", page_icon="📡")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; color: #212529; }
    .metric-box { background-color: #FFFFFF; padding: 20px; border-left: 5px solid #E63946; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .metric-title { font-size: 13px; color: #6C757D; font-weight: bold; letter-spacing: 1.5px; text-transform: uppercase; }
    .metric-value { font-size: 26px; font-weight: 900; color: #1D3557; }
    .explain-box { background-color: #FFFFFF; padding: 25px; border-left: 5px solid #457B9D; border-radius: 5px; margin-bottom: 25px; font-size: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .highlight { color: #E63946; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. Header & Introduction
# ==========================================
st.title("📡 K-PROTOCOL: 6G Omni Analysis Center")
st.markdown("#### 도심 공간 왜곡의 기하학적 환영을 99.999% 제거하는 절대 척도 엔진")
st.divider()

with st.expander("⚖️ 왜 도심 6G 측위에서 오차가 발생하는가?", expanded=True):
    st.info("""
    기존 SI 단위계의 가장 큰 맹점은 빛의 속도를 고정해 놓고 거리를 재는 순환논리입니다. 
    특히 도심의 6G 환경에서는 빌딩 고도(Z)에 따라 국소 중력이 달라지며 미세한 **기하학적 공간 왜곡**이 발생합니다.
    K-PROTOCOL은 절대 빛의 속도(C_k)와 각 기지국의 고도 기반 왜곡 지수(S_loc)를 적용하여 이 환영을 완벽히 교정합니다.
    """)

# ==========================================
# 4. Data Upload (Sidebar)
# ==========================================
st.sidebar.header("📂 데이터 직접 업로드")
st.sidebar.info("비엔나 데이터셋 파일을 아래에 순서대로 드래그 앤 드롭해 주세요.")
cell_file = st.sidebar.file_uploader("1. 기지국 데이터 (cell_info_final...)", type=["csv", "parquet"])
meas_file = st.sidebar.file_uploader("2. 측정 데이터 (scanner_measurements...)", type=["csv", "parquet"])

@st.cache_data
def load_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.parquet'):
            return pd.read_parquet(uploaded_file, engine='pyarrow')
        return pd.read_csv(uploaded_file)
    except Exception as e:
        st.sidebar.error(f"파일 읽기 오류: {e}")
        return None

# ==========================================
# 5. Core Processing & Visualization
# ==========================================
if cell_file and meas_file:
    with st.spinner("🚀 K-PROTOCOL 엔진이 시공간 좌표를 추적 중입니다..."):
        df_cell = load_uploaded_file(cell_file)
        df_meas = load_uploaded_file(meas_file)
        
        if df_cell is not None and df_meas is not None:
            # 안전장치: 컬럼 강제 형변환
            if 'height_m' in df_cell.columns:
                df_cell['height_m'] = pd.to_numeric(df_cell['height_m'], errors='coerce')
                df_cell = df_cell.dropna(subset=['height_m']).copy()
                
            time_col = next((c for c in df_meas.columns if c in ['timestamp', 'time', 'time_ns']), None)
            if time_col:
                df_meas[time_col] = pd.to_numeric(df_meas[time_col], errors='coerce')
            
            if time_col and 'cell_id_dummy' in df_cell.columns and 'cell_id_dummy' in df_meas.columns:
                # --- 1단계: K-PROTOCOL 엔진 연산 ---
                df_cell['g_loc'] = G_STD * ((R_EARTH / (R_EARTH + df_cell['height_m'])) ** 2)
                df_cell['S_loc'] = PI_SQ / df_cell['g_loc']
                
                df_merged = pd.merge(df_meas, df_cell, on='cell_id_dummy', how='inner')
                
                # 거리 보정 연산
                df_merged['SI_Dist'] = 299792458.0 * (df_merged[time_col] * 1e-9)
                df_merged['K_Dist'] = (C_K * df_merged[time_col] * 1e-9) / df_merged['S_loc']
                df_merged['Correction'] = np.abs(df_merged['SI_Dist'] - df_merged['K_Dist'])

                # --- 대시보드 메트릭 ---
                c1, c2, c3 = st.columns(3)
                c1.markdown(f'<div class="metric-box"><div class="metric-title">분석된 6G 기지국</div><div class="metric-value">{df_merged["cell_id_dummy"].nunique()} Cells</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-box"><div class="metric-title">최대 추출 왜곡량(거품)</div><div class="metric-value">{df_merged["Correction"].max():.4f} m</div></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-box"><div class="metric-title">평균 S_loc 지수</div><div class="metric-value">{df_merged["S_loc"].mean():.6f}</div></div>', unsafe_allow_html=True)

                # --- 차트 1: 도심 3D 기하학적 맵 ---
                st.markdown('<div class="explain-box">', unsafe_allow_html=True)
                st.markdown("### 🌐 [CASE 1] 도심 6G 기지국 3D 지형도 및 왜곡 지수")
                st.markdown("각 기지국의 실제 고도(Z축)에 따라 국소 왜곡 지수(S_loc)가 어떻게 분포하는지 시각화합니다.")
                
                if 'latitude' in df_cell.columns and 'longitude' in df_cell.columns:
                    fig_3d = px.scatter_3d(
                        df_cell, x='longitude', y='latitude', z='height_m',
                        color='S_loc', size_max=10, opacity=0.8,
                        color_continuous_scale='Turbo',
                        title="기지국 3D 고도 및 S_loc 분포도",
                        labels={'longitude': '경도', 'latitude': '위도', 'height_m': '고도 (m)'}
                    )
                    fig_3d.update_layout(margin=dict(l=0, r=0, b=0, t=40), template="plotly_white")
                    st.plotly_chart(fig_3d, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # --- 차트 2: 고도 vs 왜곡량 상관관계 ---
                st.markdown('<div class="explain-box">', unsafe_allow_html=True)
                st.markdown("### 📈 [CASE 2] 기하학적 환영(Correction) 추출 결과")
                st.markdown("고도가 높아질수록 기존 SI 미터법이 만들어내던 '오차 거품'이 선형적으로 증가함을 증명합니다.")
                
                # 너무 큰 데이터는 버벅임을 방지하기 위해 샘플링 처리
                plot_df = df_merged.sample(n=min(5000, len(df_merged)), random_state=42)
                
                fig_scatter = px.scatter(
                    plot_df, x='height_m', y='Correction', color='S_loc',
                    trendline="ols", trendline_color_override="#E63946",
                    title="고도 상승에 따른 SI 척도 오차(거품) 증가량",
                    labels={'height_m': '기지국 고도 (m)', 'Correction': '깎아낸 기하학적 거품 (m)'},
                    template="plotly_white"
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # --- 데이터 테이블 ---
                st.markdown("### 📄 K-PROTOCOL 정밀 보정 원본 데이터")
                display_cols = ['cell_id_dummy', 'height_m', 'S_loc', time_col, 'SI_Dist', 'K_Dist', 'Correction']
                st.dataframe(df_merged[display_cols].head(100).style.format({
                    'height_m': '{:.2f}', 'S_loc': '{:.6f}', 'SI_Dist': '{:.4f}', 'K_Dist': '{:.4f}', 'Correction': '{:.6f}'
                }), use_container_width=True)
            else:
                st.error("데이터 결합을 위한 'cell_id_dummy' 또는 시간 컬럼을 찾을 수 없습니다.")
else:
    st.info("👈 왼쪽 사이드바에 분석할 비엔나 5G/6G 데이터 2개를 차례대로 올려주세요!")
