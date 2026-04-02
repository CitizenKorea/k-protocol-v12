import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. 절대 물리 상수
C_K = 297880197.6
R_EARTH = 6371000.0
G_STD = 9.80665
PI_SQ = np.pi ** 2

# 2. 기본 UI 설정
st.set_page_config(page_title="K-PROTOCOL 6G", layout="wide")
st.title("📡 K-PROTOCOL 6G Omni Center")

# 언어 선택
lang = st.radio("Language", ["KOR", "ENG"], horizontal=True)

# 3. 사이드바 업로드
st.sidebar.header("Upload Data")
f_cell = st.sidebar.file_uploader("1. Cell Data (CSV/Parquet)", type=["csv", "parquet"])
f_meas = st.sidebar.file_uploader("2. Meas Data (CSV/Parquet)", type=["csv", "parquet"])

def load(f):
    if f is None: return None
    f.seek(0)
    return pd.read_parquet(f) if f.name.endswith('parquet') else pd.read_csv(f)

if f_cell and f_meas:
    df_c = load(f_cell)
    df_m = load(f_meas)
    
    # 컬럼 자동 탐지
    time_col = next((c for c in df_m.columns if str(c).lower() in ['timestamp', 'time', 'time_ns', 'toa']), None)
    id_col = next((c for c in ['cell_id_dummy', 'cell_id', 'gnb_id_dummy'] if c in df_c.columns and c in df_m.columns), None)

    if time_col and id_col:
        # 💡 [핵심] 에러 원천 차단: 모든 ID를 단순 문자로 통일
        df_c[id_col] = df_c[id_col].astype(str).str.replace('.0', '', regex=False).str.strip()
        df_m[id_col] = df_m[id_col].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        # 숫자 변환
        df_c['height_m'] = pd.to_numeric(df_c['height_m'], errors='coerce')
        df_m[time_col] = pd.to_numeric(df_m[time_col], errors='coerce')
        
        # 병합 및 연산
        df = pd.merge(df_m, df_cell_clean := df_c.dropna(subset=['height_m']), on=id_col, how='inner')
        
        if not df.empty:
            # K-PROTOCOL 공식 적용
            # $g_{loc} = G_{std} \cdot (\frac{R_{earth}}{R_{earth} + h})^2$
            df['g_loc'] = G_STD * ((R_EARTH / (R_EARTH + df['height_m'])) ** 2)
            df['S_loc'] = PI_SQ / df['g_loc']
            
            # $Dist_{SI} = 299792458 \cdot (time \cdot 10^{-9})$
            df['SI_Dist'] = 299792458.0 * (df[time_col] * 1e-9)
            # $Dist_K = (C_K \cdot time \cdot 10^{-9}) / S_{loc}$
            df['K_Dist'] = (C_K * df[time_col] * 1e-9) / df['S_loc']
            df['Error_m'] = (df['SI_Dist'] - df['K_Dist']).abs()

            # 결과 브리핑
            best = df.sort_values('Error_m', ascending=False).iloc[0]
            st.success("✅ Analysis Complete!")
            
            # Before & After 스토리
            if lang == "KOR":
                st.info(f"📍 가장 큰 왜곡 발견: 기지국 {best[id_col]} (고도 {best['height_m']:.1f}m)")
                st.write(f"기존 방식 오차 **{best['Error_m']:.4f}m**를 K-PROTOCOL 보정으로 제거했습니다.")
            else:
                st.info(f"📍 Max Distortion: Cell {best[id_col]} (Alt {best['height_m']:.1f}m)")
                st.write(f"SI Error **{best['Error_m']:.4f}m** has been calibrated by K-PROTOCOL.")

            # 요약 지표
            c1, c2, c3 = st.columns(3)
            c1.metric("Analyzed Cells", len(df[id_col].unique()))
            c2.metric("Max Correction", f"{df['Error_m'].max():.4f} m")
            c3.metric("Avg S_loc", f"{df['S_loc'].mean():.6f}")

            # 차트
            st.subheader("Correction Trend")
            fig = px.scatter(df.sample(min(2000, len(df))), x='height_m', y='Error_m', color='S_loc', trendline="ols")
            st.plotly_chart(fig, use_container_width=True)

            # 데이터 테이블
            st.subheader("Raw Data (Top 100)")
            st.dataframe(df[[id_col, 'height_m', 'S_loc', time_col, 'SI_Dist', 'K_Dist', 'Error_m']].head(100))
        else:
            st.error("Matching data not found.")
    else:
        st.error("Check ID or Time columns.")
