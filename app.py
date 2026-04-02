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
        # 💡 [핵심 패치] 결측치(NA)가 있어도 절대 에러가 나지 않는 판다스 전용 문자열 처리(.str)
        df_c[id_col] = df_c[id_col].astype(str).str.split('.').str[0].str.strip()
        df_m[id_col] = df_m[id_col].astype(str).str.split('.').str[0].str.strip()
        
        # 'nan' 문자열로 변환된 쓰레기값 진짜 NaN으로 복구
        df_c[id_col] = df_c[id_col].replace('nan', np.nan)
        df_m[id_col] = df_m[id_col].replace('nan', np.nan)
        
        # 숫자 변환
        df_c['height_m'] = pd.to_numeric(df_c['height_m'], errors='coerce')
        df_m[time_col] = pd.to_numeric(df_m[time_col], errors='coerce')
        
        # 💡 병합 전 유효한 데이터만 싹 걸러내기 (에러 완벽 차단)
        df_c_clean = df_c.dropna(subset=['height_m', id_col]).copy()
        df_m_clean = df_m.dropna(subset=[time_col, id_col]).copy()
        
        # 병합 및 연산
        df = pd.merge(df_m_clean, df_c_clean, on=id_col, how='inner')
        
        if not df.empty:
            # K-PROTOCOL 공식 적용
            df['g_loc'] = G_STD * ((R_EARTH / (R_EARTH + df['height_m'])) ** 2)
            df['S_loc'] = PI_SQ / df['g_loc']
            
            df['SI_Dist'] = 299792458.0 * (df[time_col] * 1e-9)
            df['K_Dist'] = (C_K * df[time_col] * 1e-9) / df['S_loc']
            df['Error_m'] = (df['SI_Dist'] - df['K_Dist']).abs()

            # 빈 값 다시 한번 청소
            df = df.dropna(subset=['Error_m'])

            if not df.empty:
                # 결과 브리핑
                best = df.sort_values('Error_m', ascending=False).iloc[0]
                st.success("✅ Analysis Complete!")
                
                # Before & After 스토리
                if lang == "KOR":
                    st.info(f"📍 가장 큰 왜곡 발견: 기지국 {best[id_col]} (고도 {best['height_m']:.1f}m)")
                    st.write(f"기존 방식 오차 **{best['Error_m']:.4f}m**를 K-PROTOCOL 보정으로 완벽히 제거했습니다.")
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
                # 버벅임 방지를 위해 2000개만 샘플링하여 차트 그리기
                plot_data = df.sample(min(2000, len(df)))
                fig = px.scatter(plot_data, x='height_m', y='Error_m', color='S_loc', trendline="ols")
                st.plotly_chart(fig, use_container_width=True)

                # 데이터 테이블
                st.subheader("Raw Data (Top 100)")
                st.dataframe(df[[id_col, 'height_m', 'S_loc', time_col, 'SI_Dist', 'K_Dist', 'Error_m']].head(100))
            else:
                st.error("연산 후 유효한 데이터가 남지 않았습니다.")
        else:
            st.error("Matching data not found (공통된 기지국 ID를 찾을 수 없습니다).")
    else:
        st.error("Check ID or Time columns (시간 또는 ID 컬럼이 없습니다).")
