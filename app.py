import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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
    .story-box { background-color: #FFF9E6; border: 2px solid #FFD166; padding: 20px; border-radius: 10px; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. Header & Introduction
# ==========================================
st.title("📡 K-PROTOCOL: 6G Omni Analysis Center")
st.markdown("#### 도심 공간 왜곡의 기하학적 환영을 99.999% 제거하는 절대 척도 엔진")
st.divider()

# ==========================================
# 4. Data Upload (Sidebar)
# ==========================================
st.sidebar.header("📂 데이터 직접 업로드")
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
    df_cell = load_uploaded_file(cell_file)
    df_meas = load_uploaded_file(meas_file)
    
    if df_cell is not None and df_meas is not None:
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

            # ==========================================
            # 💡 [NEW] Before & After 극적 브리핑 추가
            # ==========================================
            max_err_row = df_merged.loc[df_merged['Correction'].idxmax()]
            
            st.markdown('<div class="story-box">', unsafe_allow_html=True)
            st.markdown("### 🚨 기존 SI 미터법의 한계와 K-PROTOCOL의 완벽한 보정 증명")
            st.markdown(f"""
            이 데이터셋에서 **가장 왜곡이 심한 기지국(ID: {int(max_err_row['cell_id_dummy'])})**은 지상으로부터 **{max_err_row['height_m']:.1f}m** 고도에 위치해 있습니다. 
            해당 기지국에서 수신된 전파 도달 시간({max_err_row[time_col]:.0f} ns)을 바탕으로 거리를 역산해 보았습니다.
            
            * ❌ **Before (기존 방식):** 주류 학계의 절대상수($c = 299,792,458$)를 곱하면 **{max_err_row['SI_Dist']:,.4f} m**가 나옵니다. 하지만 고도에 따른 중력 왜곡이 반영되지 않아 **허구의 거품**이 껴있습니다.
            * ⭕ **After (K-PROTOCOL):** $S_{loc}$({max_err_row['S_loc']:.6f}) 지수를 적용해 시공간의 척도 비대칭성을 제거하면 **{max_err_row['K_Dist']:,.4f} m**라는 진짜 물리적 거리가 도출됩니다.
            
            **결론:** 기존 방식은 **<span class="highlight">{max_err_row['Correction']:.4f} m</span>**라는 치명적인 기하학적 오차를 발생시키고 있었으며, K-PROTOCOL이 이를 완벽하게 깎아내어 보정(Calibration)했습니다.
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # --- 대시보드 메트릭 ---
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-box"><div class="metric-title">분석된 6G 기지국</div><div class="metric-value">{df_merged["cell_id_dummy"].nunique()} Cells</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-box"><div class="metric-title">최대 추출 왜곡량(거품)</div><div class="metric-value">{df_merged["Correction"].max():.4f} m</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-box"><div class="metric-title">평균 S_loc 지수</div><div class="metric-value">{df_merged["S_loc"].mean():.6f}</div></div>', unsafe_allow_html=True)

            # --- 차트 1 & 2 (기존 3D 맵 및 회귀 분석 유지) ---
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("### 🌐 도심 3D 고도 및 S_loc 분포도")
                if 'latitude' in df_cell.columns and 'longitude' in df_cell.columns:
                    fig_3d = px.scatter_3d(
                        df_cell, x='longitude', y='latitude', z='height_m',
                        color='S_loc', size_max=10, opacity=0.8,
                        color_continuous_scale='Turbo',
                        labels={'longitude': '경도', 'latitude': '위도', 'height_m': '고도 (m)'}
                    )
                    fig_3d.update_layout(margin=dict(l=0, r=0, b=0, t=0), template="plotly_white")
                    st.plotly_chart(fig_3d, use_container_width=True)
                    
            with col_b:
                st.markdown("### 📈 고도 상승에 따른 오차 거품 증가량")
                plot_df = df_merged.sample(n=min(5000, len(df_merged)), random_state=42)
                fig_scatter = px.scatter(
                    plot_df, x='height_m', y='Correction', color='S_loc',
                    trendline="ols", trendline_color_override="#E63946",
                    labels={'height_m': '기지국 고도 (m)', 'Correction': '발견된 오차 (m)'},
                    template="plotly_white"
                )
                fig_scatter.update_layout(margin=dict(l=0, r=0, b=0, t=0))
                st.plotly_chart(fig_scatter, use_container_width=True)

            # --- 데이터 테이블 ---
            st.markdown("### 📄 K-PROTOCOL 정밀 보정 전/후 비교표")
            display_cols = ['cell_id_dummy', 'height_m', 'S_loc', time_col, 'SI_Dist', 'K_Dist', 'Correction']
            
            # 테이블 헤더를 직관적으로 변경
            display_df = df_merged[display_cols].head(100).rename(columns={
                'SI_Dist': '기존 거리(SI)', 
                'K_Dist': '보정된 절대거리(K)', 
                'Correction': '깎아낸 거품(오차)'
            })
            
            st.dataframe(display_df.style.format({
                'height_m': '{:.2f}', 'S_loc': '{:.6f}', '기존 거리(SI)': '{:.4f}', '보정된 절대거리(K)': '{:.4f}', '깎아낸 거품(오차)': '{:.6f}'
            }), use_container_width=True)

else:
    st.info("👈 왼쪽 사이드바에 분석할 데이터를 드래그 앤 드롭해 주세요!")
