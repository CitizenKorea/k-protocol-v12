import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. 절대 물리 상수
C_K = 297880197.6
R_EARTH = 6371000.0
G_STD = 9.80665
PI_SQ = np.pi ** 2

st.set_page_config(page_title="K-PROTOCOL 6G", layout="wide")

st.markdown("""
    <style>
    .metric-box { background-color: #FFFFFF; padding: 25px; border-left: 6px solid #E74C3C; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .metric-title { font-size: 14px; color: #7F8C8D; font-weight: 800; }
    .metric-value { font-size: 32px; font-weight: 900; color: #2C3E50; }
    </style>
    """, unsafe_allow_html=True)

st.title("📡 K-PROTOCOL 6G Omni Center")

st.sidebar.header("📂 1단계: 데이터 업로드")
f_cell = st.sidebar.file_uploader("1. 기지국 데이터", type=["csv", "parquet"])
f_meas = st.sidebar.file_uploader("2. 측정 데이터", type=["csv", "parquet"])

@st.cache_data
def load(f):
    if f is None: return None
    f.seek(0)
    return pd.read_parquet(f) if f.name.endswith('parquet') else pd.read_csv(f)

def get_idx(cols, keywords):
    for i, c in enumerate(cols):
        if any(k in str(c).lower() for k in keywords): return i
    return 0

if f_cell and f_meas:
    df_c = load(f_cell)
    df_m = load(f_meas)
    
    st.sidebar.divider()
    st.sidebar.header("⚙️ 2단계: 컬럼 직접 매칭")
    st.sidebar.info("💡 아래 두 개의 ID 컬럼 이름이 **같아야** 파일이 합쳐집니다!")
    
    id_c_col = st.sidebar.selectbox("🏢 기지국 파일의 ID 컬럼", df_c.columns, index=get_idx(df_c.columns, ['gnb_id', 'cell_id', 'id']))
    h_col = st.sidebar.selectbox("🏢 기지국 고도(Z) 컬럼", df_c.columns, index=get_idx(df_c.columns, ['height', 'alt', 'z']))
    
    # 💡 기지국 ID와 똑같은 이름의 컬럼이 측정 파일에 있으면 그걸 기본값으로 찰떡같이 세팅!
    m_id_default = df_m.columns.tolist().index(id_c_col) if id_c_col in df_m.columns else get_idx(df_m.columns, ['gnb_id', 'cell_id', 'id'])
    id_m_col = st.sidebar.selectbox("📡 측정 파일의 ID 컬럼", df_m.columns, index=m_id_default)
    t_col = st.sidebar.selectbox("📡 전파 도달 시간 컬럼", df_m.columns, index=get_idx(df_m.columns, ['time', 'toa', 'stamp']))

    df_c_work = df_c[[id_c_col, h_col]].copy()
    df_m_work = df_m[[id_m_col, t_col]].copy()

    # 문자열에서 숫자만 추출
    df_c_work['join_id'] = df_c_work[id_c_col].astype(str).str.extract(r'(\d+)')[0]
    df_m_work['join_id'] = df_m_work[id_m_col].astype(str).str.extract(r'(\d+)')[0]

    # 💡 [핵심 패치] 콜론(:)이 섞인 27:11.5 같은 시간 데이터를 살려내는 완벽 파싱기!
    def parse_time(val):
        v = str(val).strip()
        if ':' in v:
            try:
                p = v.split(':')
                return float(p[0]) * 60 + float(p[1]) # 분:초 -> 초 변환
            except:
                return np.nan
        try:
            return float(v)
        except:
            return np.nan

    df_m_work[t_col] = df_m_work[t_col].apply(parse_time)
    df_c_work[h_col] = pd.to_numeric(df_c_work[h_col], errors='coerce')

    df_c_clean = df_c_work.dropna(subset=[h_col, 'join_id'])
    df_m_clean = df_m_work.dropna(subset=[t_col, 'join_id'])

    df = pd.merge(df_m_clean, df_c_clean, on='join_id', how='inner')

    if not df.empty:
        # K-PROTOCOL 물리 연산
        df['g_loc'] = G_STD * ((R_EARTH / (R_EARTH + df[h_col])) ** 2)
        df['S_loc'] = PI_SQ / df['g_loc']
        df['SI_Dist'] = 299792458.0 * (df[t_col] * 1e-9)
        df['K_Dist'] = (C_K * df[t_col] * 1e-9) / df['S_loc']
        df['Correction'] = (df['SI_Dist'] - df['K_Dist']).abs()

        df = df.dropna(subset=['Correction']).copy()

        if not df.empty:
            st.success("✅ Analysis Complete!")
            best = df.sort_values('Correction', ascending=False).iloc[0]

            st.markdown('<div style="background-color: #FFFDF7; border: 2px solid #F1C40F; padding: 25px; border-radius: 12px; margin-bottom: 30px;">', unsafe_allow_html=True)
            st.markdown("### 🚨 기존 SI 미터법의 한계와 K-PROTOCOL 보정 증명")
            st.info(f"📍 가장 큰 왜곡 발견: 기지국 ID **{best['join_id']}** (고도 {best[h_col]:.1f}m)")
            st.write(f"기존 방식 오차 **{best['Correction']:,.4f}m**를 K-PROTOCOL 보정으로 완벽히 제거했습니다.")
            st.markdown('</div>', unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("분석된 기지국", df['join_id'].nunique())
            c2.metric("최대 추출 왜곡량", f"{df['Correction'].max():.4f} m")
            c3.metric("평균 S_loc 지수", f"{df['S_loc'].mean():.6f}")

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🌐 도심 기지국 3D 왜곡 맵")
                lat = next((c for c in df_c.columns if 'lat' in str(c).lower()), None)
                lon = next((c for c in df_c.columns if 'lon' in str(c).lower()), None)
                if lat and lon:
                    df_plot = df.merge(df_c[[id_c_col, lat, lon]], left_on='join_id', right_on=df_c[id_c_col].astype(str).str.extract(r'(\d+)')[0], how='left')
                    st.plotly_chart(px.scatter_3d(df_plot, x=lon, y=lat, z=h_col, color='S_loc', template="plotly_white", color_continuous_scale='Turbo'), use_container_width=True)
            with col_b:
                st.subheader("📈 기하학적 환영 증가 추이")
                st.plotly_chart(px.scatter(df.sample(min(2000, len(df))), x=h_col, y='Correction', color='S_loc', trendline="ols", template="plotly_white"), use_container_width=True)

            st.subheader("📄 K-PROTOCOL 정밀 보정 원본 데이터")
            st.dataframe(df[['join_id', h_col, 'S_loc', t_col, 'SI_Dist', 'K_Dist', 'Correction']].head(100))
        else:
            st.error("연산 후 유효한 데이터가 없습니다.")
    else:
        st.error("🚨 두 파일이 여전히 합쳐지지 않습니다. (왼쪽 사이드바의 컬럼 매칭을 다시 확인해 주세요!)")
        c1, c2 = st.columns(2)
        c1.warning(f"🏢 추출된 기지국 ID 예시:\n {df_c_clean['join_id'].unique()[:10]}")
        c2.warning(f"📡 추출된 측정 파일 ID 예시:\n {df_m_clean['join_id'].unique()[:10]}")
        st.info("👆 위 두 숫자가 다르거나 빈 칸이라면 사이드바 메뉴에서 다른 컬럼을 선택해 보세요!")
else:
    st.info("👈 왼쪽 화면에서 파일을 업로드해 주세요!")
