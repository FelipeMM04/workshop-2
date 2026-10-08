import pandas as pd
import numpy as np

def transform_spotify_data(df_raw):
    """
    Aplica las transformaciones justificadas al dataset de Spotify:
    1. Deduplicación por track_id manteniendo el registro de mayor popularidad.
    2. Remoción de columnas redundantes.
    3. Normalización de textos para la llave de integración.
    """
    df = df_raw.copy()
    
    # 1. Eliminar columna redundante de índice
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
        
    # 2. Deduplicación: Ordenar por popularidad descendente y eliminar duplicados por track_id
    df = df.sort_values(by=['track_id', 'popularity'], ascending=[True, False])
    df = df.drop_duplicates(subset=['track_id'], keep='first')
    
    # 3. Normalización de texto para la llave de integración
    df['clean_track_name'] = df['track_name'].astype(str).str.strip().str.lower()
    df['clean_artist'] = df['artists'].astype(str).str.strip().str.lower()
    df['match_key'] = df['clean_track_name'] + '||' + df['clean_artist']
    
    print(f"[TRANSFORM SPOTIFY] Registros limpios y deduplicados: {len(df):,}")
    return df

def transform_grammy_data(df_raw):
    """
    Aplica las transformaciones justificadas al dataset de los Grammy:
    1. Imputación de nulos en artist.
    2. Normalización de cadenas y creación de la llave de integración.
    """
    df = df_raw.copy()
    
    # 1. Imputación de valores faltantes en artist
    df['artist'] = df['artist'].fillna('Varios / No especificado')
    df['workers'] = df['workers'].fillna('')
    df['img'] = df['img'].fillna('')
    
    # 2. Normalización de texto para la llave de integración
    df['clean_nominee'] = df['nominee'].astype(str).str.strip().str.lower()
    df['clean_artist'] = df['artist'].astype(str).str.strip().str.lower()
    df['match_key'] = df['clean_nominee'] + '||' + df['clean_artist']
    
    print(f"[TRANSFORM GRAMMYS] Registros limpios e imputados: {len(df):,}")
    return df

def integrate_datasets(df_spotify_clean, df_grammy_clean):
    """
    Aplica el Contrato de Integración realizando el cruce entre fuentes.
    """
    print("\n[INTEGRATION] Ejecutando cruce bajo el Integration Contract...")
    
    # Cruce por la llave calculada match_key
    merged = pd.merge(
        df_spotify_clean,
        df_grammy_clean,
        on='match_key',
        how='left',
        suffixes=('_spotify', '_grammy')
    )
    
    # Marcadores analíticos de premiación
    merged['is_grammy_nominated'] = np.where(merged['year'].notnull(), 1, 0)
    merged['is_grammy_winner'] = np.where(merged['winner'] == True, 1, 0)
    
    matched_count = merged['is_grammy_nominated'].sum()
    print(f" -> Total registros consolidados: {len(merged):,}")
    print(f" -> Coincidencias con nominaciones Grammy: {matched_count:,}")
    
    return merged

if __name__ == "__main__":
    # Test rápido de integración
    df_sp_raw = pd.read_csv("data/raw/spotify_dataset.csv")
    df_sp_clean = transform_spotify_data(df_sp_raw)
    
    import psycopg2
    conn = psycopg2.connect(dbname="music_dw", user="postgres", password="postgres", host="localhost", port="5432")
    df_gr_raw = pd.read_sql_query("SELECT * FROM raw_grammys;", conn)
    conn.close()
    
    df_gr_clean = transform_grammy_data(df_gr_raw)
    df_integrated = integrate_datasets(df_sp_clean, df_gr_clean)