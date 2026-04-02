import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ==============================================================================
# 1. 물리 상수 세팅 (K-PROTOCOL)
# ==============================================================================
C_K = 297880197.6      
R_EARTH = 6371000.0    
G_STD = 9.80665        
PI_SQ = np.pi ** 2     

# ==============================================================================
# 2. UI 및 페이지 설정
# ==============================================================================
st.set_page_config(page_title="K-PROTOCOL 6G Omni Center", layout="wide", page_icon="📡")

st.markdown("""
    <style>
    .stApp { background-color: #F4F6F9; color: #2C3E50; }
    .metric-box { background-color: #FFFFFF; padding: 25px; border-left: 6px solid #E74C3C; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 10px 15px rgba(0,0,0,0.05); }
    .metric-title { font-size: 14px; color: #7F8C8D; font-weight: 800; letter-spacing: 1.5px; }
    .metric-value { font-size: 32px; font-weight: 900; color: #2C3E50; }
    .explain-box { background-color: #FFFFFF; padding: 30px; border-left: 6px solid #3498DB; border-radius: 8px; margin-bottom: 30px; }
    .story-box { background-color: #FFFDF7; border: 2px solid #F1C40F; padding: 25px; border-radius: 12px; margin-bottom: 30px; line-height: 1.8;}
    .highlight { color: #E74C3C; font-weight: 900; background-color: #FDEDEC; padding: 2px 6px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

col_title, col_lang = st.columns([8, 1])
with col_lang:
    lang = st.radio("Lang", ["KOR", "ENG"], horizontal=True, label_visibility="collapsed")

if lang == "KOR":
    st.markdown("# 📡 K-PROTOCOL: 6G Omni Analysis Center")
    st.markdown("#### 도심 공간 왜곡의 기하학적 환영을 99.999% 제거하는 절대 척도 엔진")
else:
    st.markdown("# 📡 K-PROTOCOL: 6G Omni Analysis Center")
    st.markdown("#### Absolute Metric Engine eliminating 99.999% of geometric illusions")

st.divider()

# ==============================================================================
# 3. 데이터 로드 및 결합 (초강력 방탄 로직)
# ==============================================================================
st.sidebar.header("📂 Data Upload")
cell_file = st.sidebar.file_uploader("1. Cell Data (csv, parquet)", type=["csv", "parquet"])
meas_file = st.sidebar.file_uploader("2. Meas Data (csv, parquet)", type=["csv", "parquet"])

def safe_load(f):
    if f is None: return None
    try:
        f.seek(0)
        return pd.read_parquet(f) if f.name.endswith('.parquet') else pd.read_csv(f)
    except Exception as e:
        st.sidebar.error(f"Load Error: {e}")
        return None

if cell_file and meas_file:
    df_c = safe_load(cell_file)
    df_m = safe_load(meas_file)
    
    if df_c is not None and df_m is not None:
        # 컬럼 스캔
        time_col = next((c for c in df_m.columns if str(c).lower() in ['timestamp', 'time', 'time_ns', 'toa']), None)
        id_col = next((c for c in ['cell_id_dummy', 'cell_id', 'gnb_id_dummy'] if c in df_c.columns and c in df_m.columns), None)

        if time_col and id_col:
            
            # 💡 [핵심 패치 1] 가장 원시적이고 확실한 ID 통일 (정규식/함수 충돌 완전 제거)
            # 숫자 1.0 이든 문자 "1"이든 무조건 문자열로 바꾼 뒤 소수점 이하는 잘라버림
            df_c[id_col] = df_c[id_col].astype(str).apply(lambda x: x.split('.')[0].strip())
            df_m[id_col] = df_m[id_col].astype(str).apply(lambda x: x.split('.')[0].strip())
            
            # 💡 [핵심 패치 2] 숫자 강제 변환 (에러 무시 옵션 대신 NaN 처리 후 삭제)
            df_c['height_m'] = pd.to_numeric(df_c.get('height_m', np.nan), errors='coerce')
            df_m[time_col] = pd.to_numeric(df_m[time_col], errors='coerce')
            
            df_c = df_c.dropna(subset=['height_m', id_col])
            df_m = df_m.dropna(subset=[time_col, id_col])
            
            # 공통 컬럼 제거 (ID 제외) 후 병합
            common_cols = list(set(df_m.columns) & set(df_c.columns) - {id_col})
            df_m_clean = df_m.drop(columns=common_cols)
            df = pd.merge(df_m_clean, df_c, on=id_col, how='inner')
            
            if not df.empty:
                
                # ==============================================================
                # 4. K-PROTOCOL 연산 코어
                # ==============================================================
                df['g_loc'] = G_STD * ((R_EARTH / (R_EARTH + df['height_m'])) ** 2)
                df['S_loc'] = PI_SQ / df['g_loc']
                df['SI_Dist'] = 299792458.0 * (df[time_col] * 1e-9)
                df['K_Dist'] = (C_K * df[time_col] * 1e-9) / df['S_loc']
                df['Correction'] = (df['SI_Dist'] - df['K_Dist']).abs()
                
                df = df.dropna(subset=['Correction']).copy()
                
                if not df.empty:
                    
                    # ==============================================================
                    # 5. 결과 시각화 및 대시보드
                    # ==============================================================
                    best = df.sort_values('Correction', ascending=False).iloc[0]
                    
                    st.markdown('<div class="story-box">', unsafe_allow_html=True)
                    if lang == "KOR":
                        st.markdown(f"### 🚨 기존 SI 미터법의 한계와 K-PROTOCOL 보정 증명")
                        st.markdown(f"가장 왜곡이 심한 기지국(ID: **{best[id_col]}**)은 고도 **{best['height_m']:.1f}m**에 위치합니다. 기존 SI 미터법은 **<span class='highlight'>{best['Correction']:.4f} m</span>**라는 치명적인 거품 오차를 발생시켰으나, K-PROTOCOL이 이를 완벽히 보정했습니다.", unsafe_allow_html=True)
                    else:
                        st.markdown(f"### 🚨 SI Limits & K-PROTOCOL Calibration")
                        st.markdown(f"The most distorted cell (ID: **{best[id_col]}**) is at **{best['height_m']:.1f}m** altitude. K-PROTOCOL successfully extracted a severe error bubble of **<span class='highlight'>{best['Correction']:.4f} m</span>** generated by the SI metric.", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f'<div class="metric-box"><div class="metric-title">{"분석된 기지국" if lang=="KOR" else "Analyzed Cells"}</div><div class="metric-value">{df[id_col].nunique()}</div></div>', unsafe_allow_html=True)
                    c2.markdown(f'<div class="metric-box"><div class="metric-title">{"최대 추출 왜곡량" if lang=="KOR" else "Max Correction"}</div><div class="metric-value">{df["Correction"].max():.4f} m</div></div>', unsafe_allow_html=True)
                    c3.markdown(f'<div class="metric-box"><div class="metric-title">{"평균 S_loc 지수" if lang=="KOR" else "Avg S_loc"}</div><div class="metric-value">{df["S_loc"].mean():.6f}</div></div>', unsafe_allow_html=True)

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"### {'🌐 도심 기지국 3D 지형도' if lang=='KOR' else '🌐 3D Topography'}")
                        lat = next((c for c in df.columns if 'latitude' in str(c).lower()), None)
                        lon = next((c for c in df.columns if 'longitude' in str(c).lower()), None)
                        if lat and lon:
                            fig3d = px.scatter_3d(df, x=lon, y=lat, z='height_m', color='S_loc', template="plotly_white", color_continuous_scale='Turbo')
                            fig3d.update_layout(margin=dict(l=0, r=0, b=0, t=0))
                            st.plotly_chart(fig3d, use_container_width=True)
                    with col_b:
                        st.markdown(f"### {'📈 기하학적 환영 증가 추이' if lang=='KOR' else '📈 Geometric Illusion Trend'}")
                        fig_scat = px.scatter(df.sample(min(5000, len(df))), x='height_m', y='Correction', color='S_loc', trendline="ols", template="plotly_white")
                        fig_scat.update_layout(margin=dict(l=0, r=0, b=0, t=0))
                        st.plotly_chart(fig_scat, use_container_width=True)

                    st.markdown(f"### {'📄 K-PROTOCOL 정밀 보정 원본 데이터' if lang=='KOR' else '📄 Calibration Data'}")
                    st.dataframe(df[[id_col, 'height_m', 'S_loc', time_col, 'SI_Dist', 'K_Dist', 'Correction']].head(1000).style.format({
                        'height_m': '{:.2f}', 'S_loc': '{:.6f}', 'SI_Dist': '{:.4f}', 'K_Dist': '{:.4f}', 'Correction': '{:.6f}'
                    }), use_container_width=True)

                else:
                    st.error("🚨 연산 후 유효한 데이터가 없습니다." if lang=="KOR" else "🚨 No valid data after computation.")
            else:
                st.error("🚨 공통 기지국 ID를 기반으로 데이터를 병합할 수 없습니다." if lang=="KOR" else "🚨 Failed to merge data based on Cell ID.")
        else:
            st.error("🚨 시간 컬럼 또는 기지국 ID 컬럼을 찾을 수 없습니다." if lang=="KOR" else "🚨 Time or ID column not found.")
else:
    st.info("👈 데이터를 업로드해 주세요! / Please upload data." if lang=="KOR" else "👈 Please upload data.")
