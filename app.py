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
st.title("📡 K-PROTOCOL 6G Omni Center")

st.sidebar.header("📂 Data Upload")
f_cell = st.sidebar.file_uploader("1. Cell Data", type=["csv", "parquet"])
f_meas = st.sidebar.file_uploader("2. Meas Data", type=["csv", "parquet"])

def load(f):
    if f is None: return None
    f.seek(0)
    return pd.read_parquet(f) if f.name.endswith('parquet') else pd.read_csv(f)

if f_cell and f_meas:
    df_c = load(f_cell)
    df_m = load(f_meas)
    
    # [핵심 1] 유연한 컬럼 탐지기 (대소문자, 이름 섞임 완벽 방어)
    time_col = next((c for c in df_m.columns if 'time' in c.lower() or 'toa' in c.lower() or 'stamp' in c.lower()), None)
    id_col = next((c for c in df_c.columns if 'id' in c.lower() and c in df_m.columns), None)
    height_col = next((c for c in df_c.columns if 'height' in c.lower() or 'alt' in c.lower() or c.lower() == 'z'), None)

    if time_col and id_col and height_col:
        # 💡 [핵심 2] 문자열 조작 버리고, 순수 숫자로 강제 통일 (에러 0%)
        # 1.0 이든 "1" 이든 무조건 같은 숫자 1로 인식하게 만듦
        df_c[id_col] = pd.to_numeric(df_c[id_col], errors='coerce')
        df_m[id_col] = pd.to_numeric(df_m[id_col], errors='coerce')
        
        df_c[height_col] = pd.to_numeric(df_c[height_col], errors='coerce')
        df_m[time_col] = pd.to_numeric(df_m[time_col], errors='coerce')
        
        # 결측치 제거 후 병합
        df_c_clean = df_c.dropna(subset=[height_col, id_col])
        df_m_clean = df_m.dropna(subset=[time_col, id_col])
        
        df = pd.merge(df_m_clean, df_c_clean, on=id_col, how='inner')
        
        if not df.empty:
            # K-PROTOCOL 물리 연산
            df['g_loc'] = G_STD * ((R_EARTH / (R_EARTH + df[height_col])) ** 2)
            df['S_loc'] = PI_SQ / df['g_loc']
            df['SI_Dist'] = 299792458.0 * (df[time_col] * 1e-9)
            df['K_Dist'] = (C_K * df[time_col] * 1e-9) / df['S_loc']
            df['Correction'] = (df['SI_Dist'] - df['K_Dist']).abs()
            
            df = df.dropna(subset=['Correction'])
            
            # 시각화 및 결과
            st.success("✅ Analysis Complete!")
            best = df.sort_values('Correction', ascending=False).iloc[0]
            st.info(f"📍 가장 큰 왜곡: 기지국 ID {best[id_col]} (고도 {best[height_col]:.1f}m) -> 기존 방식 오차 {best['Correction']:.4f}m를 완벽 보정")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Analyzed Cells", df[id_col].nunique())
            c2.metric("Max Correction", f"{df['Correction'].max():.4f} m")
            c3.metric("Avg S_loc", f"{df['S_loc'].mean():.6f}")

            col_a, col_b = st.columns(2)
            with col_a:
                lat = next((c for c in df.columns if 'lat' in str(c).lower()), None)
                lon = next((c for c in df.columns if 'lon' in str(c).lower()), None)
                if lat and lon:
                    st.plotly_chart(px.scatter_3d(df, x=lon, y=lat, z=height_col, color='S_loc', template="plotly_white", color_continuous_scale='Turbo'), use_container_width=True)
            with col_b:
                st.plotly_chart(px.scatter(df.sample(min(2000, len(df))), x=height_col, y='Correction', color='S_loc', trendline="ols", template="plotly_white"), use_container_width=True)
                
            st.dataframe(df[[id_col, height_col, 'S_loc', time_col, 'SI_Dist', 'K_Dist', 'Correction']].head(100))
        else:
            # 💡 [핵심 3] X-Ray 디버거 작동! (눈 뜬 장님 탈출)
            st.error("🚨 두 파일이 합쳐지지 않았습니다! ID 형식이 서로 다릅니다.")
            col1, col2 = st.columns(2)
            col1.warning(f"🏢 기지국 파일의 ID 예시:\n {df_c_clean[id_col].unique()[:10]}")
            col2.warning(f"📡 측정 파일의 ID 예시:\n {df_m_clean[id_col].unique()[:10]}")
            st.info("👆 위 두 숫자가 어떻게 다른지 확인해 주세요. (예: 한쪽은 NaN이거나 단위가 다름)")
    else:
        st.error(f"🚨 필수 컬럼을 찾을 수 없습니다! (발견된 컬럼 - 시간: {time_col}, ID: {id_col}, 고도: {height_col})")
