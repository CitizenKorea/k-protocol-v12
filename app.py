import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ==============================================================================
# 1. K-PROTOCOL Universal Physical Constants
# ==============================================================================
C_K = 297880197.6
R_EARTH = 6371000.0
G_STD = 9.80665
PI_SQ = np.pi ** 2

# ==============================================================================
# 2. Page Configuration & Custom CSS
# ==============================================================================
st.set_page_config(page_title="K-PROTOCOL 6G Omni Center", layout="wide", page_icon="📡")

st.markdown("""
    <style>
    .stApp { background-color: #F4F6F9; color: #2C3E50; }
    .metric-box { background-color: #FFFFFF; padding: 25px; border-left: 6px solid #E74C3C; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .metric-title { font-size: 14px; color: #7F8C8D; font-weight: 800; letter-spacing: 1px;}
    .metric-value { font-size: 32px; font-weight: 900; color: #2C3E50; }
    .story-box { background-color: #FFFDF7; border: 2px solid #F1C40F; padding: 25px; border-radius: 12px; margin-bottom: 30px; line-height: 1.6;}
    .highlight { color: #E74C3C; font-weight: 900; background-color: #FDEDEC; padding: 2px 6px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. Bilingual Dictionary (한/영 완벽 사전)
# ==============================================================================
i18n = {
    'KOR': {
        'title': "📡 K-PROTOCOL: 6G Omni Analysis Center",
        'subtitle': "#### 도심 공간 왜곡의 기하학적 환영을 99.999% 제거하는 절대 척도 엔진",
        'sb_title1': "📂 1단계: 데이터 업로드",
        'sb_title2': "⚙️ 2단계: 컬럼 매칭",
        'f_cell': "1. 기지국 데이터 (cell_info)",
        'f_meas': "2. 측정 데이터 (scanner_meas)",
        'col_c_id': "🏢 기지국 ID 컬럼",
        'col_c_h': "🏢 기지국 고도(Z) 컬럼",
        'col_m_id': "📡 측정 파일 ID 컬럼",
        'err_empty': "🚨 연산 가능한 유효 데이터가 없습니다. (ID 매칭 실패)",
        'story_title': "🚨 기존 SI 미터법의 한계와 K-PROTOCOL 보정 증명",
        'm_cell': "분석된 기지국 수",
        'm_max': "최대 추출 왜곡 (1km당)",
        'm_avg': "도심 평균 S_loc 지수",
        'c1_title': "🌐 도심 기지국 3D 왜곡 분포",
        'c2_title': "📈 고도 상승에 따른 환영(Correction) 증가량",
        'c2_desc': "신호가 1km 진행할 때마다 발생하는 고도별 척도 오차의 선형적 증가를 증명합니다.",
        'tbl_title': "📄 K-PROTOCOL 정밀 보정 원본 데이터 (1km 기준)"
    },
    'ENG': {
        'title': "📡 K-PROTOCOL: 6G Omni Analysis Center",
        'subtitle': "#### Absolute Metric Engine eliminating 99.999% of geometric illusions",
        'sb_title1': "📂 Step 1: Data Upload",
        'sb_title2': "⚙️ Step 2: Column Mapping",
        'f_cell': "1. Cell Data (cell_info)",
        'f_meas': "2. Measurement Data (scanner_meas)",
        'col_c_id': "🏢 Cell ID Column",
        'col_c_h': "🏢 Cell Altitude (Z) Column",
        'col_m_id': "📡 Measurement ID Column",
        'err_empty': "🚨 No valid data available for computation. (ID matching failed)",
        'story_title': "🚨 Limits of SI Metric & K-PROTOCOL Calibration",
        'm_cell': "Analyzed Cells",
        'm_max': "Max Distortion (per 1km)",
        'm_avg': "Average Urban S_loc",
        'c1_title': "🌐 3D Topography & Distortion Distribution",
        'c2_title': "📈 Geometric Illusion Trend by Altitude",
        'c2_desc': "Proves the linear increase in scale error per 1km of signal propagation across altitudes.",
        'tbl_title': "📄 K-PROTOCOL Calibration Data (Based on 1km)"
    }
}

# ==============================================================================
# 4. Interface & Language Toggle
# ==============================================================================
col_title, col_lang = st.columns([8, 1])
with col_lang:
    lang = st.radio("Language", ["KOR", "ENG"], horizontal=True, label_visibility="collapsed")
t = i18n[lang]

with col_title:
    st.markdown(f"# {t['title']}")
    st.markdown(t['subtitle'])
st.divider()

# ==============================================================================
# 5. Data Upload & Processing Engine
# ==============================================================================
st.sidebar.header(t['sb_title1'])
f_cell = st.sidebar.file_uploader(t['f_cell'], type=["csv", "parquet"])
f_meas = st.sidebar.file_uploader(t['f_meas'], type=["csv", "parquet"])

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
    st.sidebar.header(t['sb_title2'])
    
    id_c_col = st.sidebar.selectbox(t['col_c_id'], df_c.columns, index=get_idx(df_c.columns, ['gnb_id', 'cell_id']))
    h_col = st.sidebar.selectbox(t['col_c_h'], df_c.columns, index=get_idx(df_c.columns, ['height', 'alt', 'z']))
    id_m_col = st.sidebar.selectbox(t['col_m_id'], df_m.columns, index=get_idx(df_m.columns, ['gnb_id', 'cell_id']))

    # 데이터 복사본 생성 및 ID 강제 정수 변환 (에러 완전 차단)
    df_c_work = df_c[[id_c_col, h_col]].copy()
    df_m_work = df_m[[id_m_col]].copy()

    df_c_work['join_id'] = pd.to_numeric(df_c_work[id_c_col], errors='coerce')
    df_m_work['join_id'] = pd.to_numeric(df_m_work[id_m_col], errors='coerce')

    df_c_work = df_c_work.dropna(subset=['join_id'])
    df_m_work = df_m_work.dropna(subset=['join_id'])
    
    df_c_work['join_id'] = df_c_work['join_id'].astype(int)
    df_m_work['join_id'] = df_m_work['join_id'].astype(int)
    df_c_work[h_col] = pd.to_numeric(df_c_work[h_col], errors='coerce')
    df_c_work = df_c_work.dropna(subset=[h_col])

    # 데이터 병합
    df = pd.merge(df_m_work, df_c_work, on='join_id', how='inner')

    if not df.empty:
        # ==============================================================
        # 💡 1km (1000m) 기준 상대 왜곡량 연산 엔진
        # ==============================================================
        df['g_loc'] = G_STD * ((R_EARTH / (R_EARTH + df[h_col])) ** 2)
        df['S_loc'] = PI_SQ / df['g_loc']
        
        REFERENCE_DIST = 1000.0 # 1km 기준
        df['SI_Dist'] = REFERENCE_DIST
        df['K_Dist'] = REFERENCE_DIST / df['S_loc']
        df['Correction'] = (df['SI_Dist'] - df['K_Dist']).abs()

        df = df.dropna(subset=['Correction']).copy()

        if not df.empty:
            best = df.sort_values('Correction', ascending=False).iloc[0]

            st.markdown('<div class="story-box">', unsafe_allow_html=True)
            st.markdown(f"### {t['story_title']}")
            if lang == "KOR":
                st.info(f"📍 가장 큰 왜곡 발생 지역: 기지국 ID **{best['join_id']}** (고도 {best[h_col]:.1f}m)")
                st.write(f"해당 고도에서 신호가 1km(1,000m) 진행할 때마다, 기존 미터법은 **<span class='highlight'>{best['Correction']:.6f} m</span>**의 기하학적 거품 오차를 발생시키며, K-PROTOCOL이 이를 완벽히 보정했습니다.", unsafe_allow_html=True)
            else:
                st.info(f"📍 Max Distortion Area: Cell ID **{best['join_id']}** (Altitude {best[h_col]:.1f}m)")
                st.write(f"For every 1km of signal propagation at this altitude, the SI metric generates a geometric error bubble of **<span class='highlight'>{best['Correction']:.6f} m</span>**, which is perfectly calibrated by K-PROTOCOL.", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-box"><div class="metric-title">{t["m_cell"]}</div><div class="metric-value">{df["join_id"].nunique()}</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-box"><div class="metric-title">{t["m_max"]}</div><div class="metric-value">{df["Correction"].max():.6f} m</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-box"><div class="metric-title">{t["m_avg"]}</div><div class="metric-value">{df["S_loc"].mean():.6f}</div></div>', unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader(t['c1_title'])
                lat = next((c for c in df_c.columns if 'lat' in str(c).lower()), None)
                lon = next((c for c in df_c.columns if 'lon' in str(c).lower()), None)
                if lat and lon:
                    df_plot = df.merge(df_c[[id_c_col, lat, lon]], left_on='join_id', right_on=pd.to_numeric(df_c[id_c_col], errors='coerce').fillna(-1).astype(int), how='left')
                    st.plotly_chart(px.scatter_3d(df_plot, x=lon, y=lat, z=h_col, color='S_loc', template="plotly_white", color_continuous_scale='Turbo'), use_container_width=True)
                else:
                    st.warning("위도(Latitude) / 경도(Longitude) 데이터가 없어 3D 맵을 생성할 수 없습니다." if lang=="KOR" else "Missing coordinates for 3D map.")
            with col_b:
                st.subheader(t['c2_title'])
                st.caption(t['c2_desc'])
                # statsmodels ModuleNotFoundError 방지를 위해 trendline="ols" 제거
                st.plotly_chart(px.scatter(df.sample(min(2000, len(df))), x=h_col, y='Correction', color='S_loc', template="plotly_white"), use_container_width=True)

            st.subheader(t['tbl_title'])
            display_cols = ['join_id', h_col, 'S_loc', 'SI_Dist', 'K_Dist', 'Correction']
            st.dataframe(df[display_cols].head(100).style.format({
                h_col: '{:.2f}', 'S_loc': '{:.6f}', 'SI_Dist': '{:.1f}', 'K_Dist': '{:.6f}', 'Correction': '{:.6f}'
            }), use_container_width=True)
            
        else:
            st.error(t['err_empty'])
    else:
        st.error(t['err_empty'])
else:
    st.info("👈 데이터를 업로드해 주세요! / Please upload data files." if lang=="KOR" else "👈 Please upload data files.")
