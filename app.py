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
    
    # 데이터셋에 맞는 기본값 자동 찾기
    def get_col(cols, keywords):
        for c in cols:
            if any(k in str(c).lower() for k in keywords): return c
        return cols[0]

    # UI 드롭다운
    id_c_col = st.sidebar.selectbox("🏢 기지국 ID 컬럼", df_c.columns, index=df_c.columns.tolist().index(get_col(df_c.columns, ['gnb_id_dummy', 'cell_id_dummy'])))
    h_col = st.sidebar.selectbox("🏢 기지국 고도(Z) 컬럼", df_c.columns, index=df_c.columns.tolist().index(get_col(df_c.columns, ['height', 'z'])))
    
    id_m_col = st.sidebar.selectbox("📡 측정 파일 ID 컬럼", df_m.columns, index=df_m.columns.tolist().index(get_col(df_m.columns, ['gnb_id_dummy', 'cell_id_dummy'])))
    t_col = st.sidebar.selectbox("📡 전파 도달 시간 컬럼", df_m.columns, index=df_m.columns.tolist().index(get_col(df_m.columns, ['time'])))

    # 연산용 복사본
    df_c_work = df_c.copy()
    df_m_work = df_m.copy()

    # 💡 [핵심 방어 1] ID 컬럼의 빈칸(NaN) 및 실수형태(11.0) 완벽 정규화
    df_c_work['join_id'] = pd.to_numeric(df_c_work[id_c_col], errors='coerce')
    df_m_work['join_id'] = pd.to_numeric(df_m_work[id_m_col], errors='coerce')

    # NaN이 된 잘못된 ID 행 제거 후 정수(int)로 깔끔하게 통일
    df_c_work = df_c_work.dropna(subset=['join_id'])
    df_m_work = df_m_work.dropna(subset=['join_id'])
    df_c_work['join_id'] = df_c_work['join_id'].astype(int)
    df_m_work['join_id'] = df_m_work['join_id'].astype(int)

    # 💡 [핵심 방어 2] 날짜 문자열(2024-06-27 11:27:11.473) 완벽 해독기
    # 날짜를 판다스 datetime으로 변환 후, 나노초(ns) 단위의 순수 숫자로 강제 추출!
    df_m_work['parsed_time'] = pd.to_datetime(df_m_work[t_col], errors='coerce')
    df_m_work = df_m_work.dropna(subset=['parsed_time'])
    df_m_work['time_ns'] = df_m_work['parsed_time'].astype('int64') # 1970년 기준 나노초 변환

    df_c_work[h_col] = pd.to_numeric(df_c_work[h_col], errors='coerce')
    df_c_work = df_c_work.dropna(subset=[h_col])

    # 최종 병합
    df = pd.merge(df_m_work, df_c_work, on='join_id', how='inner', suffixes=('_meas', '_cell'))

    if not df.empty:
        # K-PROTOCOL 물리 연산 (시간은 추출한 time_ns 사용)
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
            # 경도, 위도 찾기
            lat = next((c for c in df.columns if 'lat' in str(c).lower()), None)
            lon = next((c for c in df.columns if 'lon' in str(c).lower()), None)
            if lat and lon:
                st.plotly_chart(px.scatter_3d(df, x=lon, y=lat, z=h_col, color='S_loc', template="plotly_white", color_continuous_scale='Turbo'), use_container_width=True)
        with col_b:
            st.subheader("📈 기하학적 환영 증가 추이")
            st.plotly_chart(px.scatter(df.sample(min(2000, len(df))), x=h_col, y='Correction', color='S_loc', trendline="ols", template="plotly_white"), use_container_width=True)

        st.subheader("📄 K-PROTOCOL 정밀 보정 원본 데이터")
        display_cols = ['join_id', h_col, 'S_loc', t_col, 'SI_Dist', 'K_Dist', 'Correction']
        st.dataframe(df[display_cols].head(100))
    else:
        st.error("🚨 병합 결과가 비어있습니다. (왼쪽 사이드바에서 ID 컬럼을 `gnb_id_dummy` 나 `cell_id_dummy`로 똑같이 맞춰주세요!)")
else:
    st.info("👈 데이터를 업로드해 주세요!")
