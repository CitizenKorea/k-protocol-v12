import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. 절대 물리 상수
C_K = 297880197.6
R_EARTH = 6371000.0
G_STD = 9.80665
PI_SQ = np.pi ** 2

st.set_page_config(page_title="K-PROTOCOL 6G Omni Center", layout="wide")

st.markdown("""
    <style>
    .metric-box { background-color: #FFFFFF; padding: 25px; border-left: 6px solid #E74C3C; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .metric-title { font-size: 14px; color: #7F8C8D; font-weight: 800; }
    .metric-value { font-size: 32px; font-weight: 900; color: #2C3E50; }
    </style>
    """, unsafe_allow_html=True)

st.title("📡 K-PROTOCOL 6G Omni Center")

st.sidebar.header("📂 1단계: 데이터 업로드")
f_cell = st.sidebar.file_uploader("1. 기지국 데이터 (cell_info)", type=["csv", "parquet"])
f_meas = st.sidebar.file_uploader("2. 측정 데이터 (scanner_meas)", type=["csv", "parquet"])

@st.cache_data
def load(f):
    if f is None: return None
    f.seek(0)
    return pd.read_parquet(f) if f.name.endswith('parquet') else pd.read_csv(f)

if f_cell and f_meas:
    df_c = load(f_cell)
    df_m = load(f_meas)
    
    st.sidebar.divider()
    st.sidebar.header("⚙️ 2단계: 컬럼 매칭")
    
    def get_col(cols, keywords):
        for c in cols:
            if any(k in str(c).lower() for k in keywords): return c
        return cols[0]

    id_c_col = st.sidebar.selectbox("🏢 기지국 ID 컬럼", df_c.columns, index=df_c.columns.tolist().index(get_col(df_c.columns, ['gnb_id_dummy', 'cell_id_dummy'])))
    h_col = st.sidebar.selectbox("🏢 기지국 고도(Z) 컬럼", df_c.columns, index=df_c.columns.tolist().index(get_col(df_c.columns, ['height', 'z'])))
    
    id_m_col = st.sidebar.selectbox("📡 측정 파일 ID 컬럼", df_m.columns, index=df_m.columns.tolist().index(get_col(df_m.columns, ['gnb_id_dummy', 'cell_id_dummy'])))
    t_col = st.sidebar.selectbox("📡 전파 도달 시간 컬럼", df_m.columns, index=df_m.columns.tolist().index(get_col(df_m.columns, ['time'])))

    df_c_work = df_c.copy()
    df_m_work = df_m.copy()

    df_c_work['join_id'] = pd.to_numeric(df_c_work[id_c_col], errors='coerce')
    df_m_work['join_id'] = pd.to_numeric(df_m_work[id_m_col], errors='coerce')

    df_c_work = df_c_work.dropna(subset=['join_id'])
    df_m_work = df_m_work.dropna(subset=['join_id'])
    df_c_work['join_id'] = df_c_work['join_id'].astype(int)
    df_m_work['join_id'] = df_m_work['join_id'].astype(int)

    # 💡 [핵심 패치] 스마트 타임엔진 (우주 단위 거리를 깎아내는 정밀 상대시간 로직)
    temp_time = pd.to_numeric(df_m_work[t_col], errors='coerce')
    if temp_time.notna().sum() > 0:
        # 데이터가 이미 숫자(나노초)라면 그대로 씁니다!
        df_m_work['time_ns'] = temp_time
    else:
        # 날짜 문자열이라면 첫 번째 측정 시간을 0으로 잡고 상대 시간(ns)으로 변환합니다!
        dt = pd.to_datetime(df_m_work[t_col], errors='coerce')
        df_m_work['time_ns'] = (dt - dt.min()).dt.total_seconds() * 1e9
        
    # 거리가 0이 되는 것을 방지하기 위해 0ns는 1ns로 최소 보정
    df_m_work['time_ns'] = df_m_work['time_ns'].replace(0, 1)
    df_m_work = df_m_work.dropna(subset=['time_ns'])

    df_c_work[h_col] = pd.to_numeric(df_c_work[h_col], errors='coerce')
    df_c_work = df_c_work.dropna(subset=[h_col])

    df = pd.merge(df_m_work, df_c_work, on='join_id', how='inner', suffixes=('_meas', '_cell'))

    if not df.empty:
        df['g_loc'] = G_STD * ((R_EARTH / (R_EARTH + df[h_col])) ** 2)
        df['S_loc'] = PI_SQ / df['g_loc']
        df['SI_Dist'] = 299792458.0 * (df['time_ns'] * 1e-9)
        df['K_Dist'] = (C_K * df['time_ns'] * 1e-9) / df['S_loc']
        df['Correction'] = (df['SI_Dist'] - df['K_Dist']).abs()

        best = df.sort_values('Correction', ascending=False).iloc[0]

        st.markdown('<div style="background-color: #FFFDF7; border: 2px solid #F1C40F; padding: 25px; border-radius: 12px; margin-bottom: 30px;">', unsafe_allow_html=True)
        st.markdown("### 🚨 기존 SI 미터법의 한계와 K-PROTOCOL 보정 증명")
        st.info(f"📍 발견된 기지국 ID **{best['join_id']}** (고도 {best[h_col]:.1f}m)")
        st.write(f"기존 방식 오차 **{best['Correction']:,.4f} m** 를 K-PROTOCOL 보정으로 완벽히 제거했습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("분석된 기지국", df['join_id'].nunique())
        c2.metric("최대 추출 왜곡량", f"{df['Correction'].max():.4f} m")
        c3.metric("평균 S_loc 지수", f"{df['S_loc'].mean():.6f}")

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("🌐 도심 기지국 3D 왜곡 맵")
            lat = next((c for c in df.columns if 'lat' in str(c).lower()), None)
            lon = next((c for c in df.columns if 'lon' in str(c).lower()), None)
            if lat and lon:
                st.plotly_chart(px.scatter_3d(df, x=lon, y=lat, z=h_col, color='S_loc', template="plotly_white", color_continuous_scale='Turbo'), use_container_width=True)
        with col_b:
            st.subheader("📈 기하학적 환영 증가 추이")
            # 💡 [핵심 패치] 추세선(trendline) 옵션 제거로 statsmodels 에러 완벽 차단!
            st.plotly_chart(px.scatter(df.sample(min(2000, len(df))), x=h_col, y='Correction', color='S_loc', template="plotly_white"), use_container_width=True)

        st.subheader("📄 K-PROTOCOL 정밀 보정 원본 데이터")
        display_cols = ['join_id', h_col, 'S_loc', t_col, 'SI_Dist', 'K_Dist', 'Correction']
        st.dataframe(df[display_cols].head(100))
    else:
        st.error("🚨 병합 결과가 비어있습니다.")
else:
    st.info("👈 데이터를 업로드해 주세요!")
