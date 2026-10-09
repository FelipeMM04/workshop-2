import psycopg2
import pandas as pd
import numpy as np

def connect_db():
    return psycopg2.connect(
        dbname="music_dw",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )

def safe_str(val, max_len=500, default=None):
    """Trunca de forma segura las cadenas de texto y aplica valor por defecto si es nulo."""
    if pd.isnull(val) or val is None:
        return default
    s = str(val).strip()
    if not s:
        return default
    return s[:max_len] if len(s) > max_len else s

def load_data_warehouse(df_integrated):
    """
    Carga los datos preparados y validados en el Data Warehouse Kimball (Esquema en Estrella).
    Poblando secuencialmente: dim_track, dim_artist, dim_genre, dim_grammy_award y fact_music_performance.
    """
    print("\n" + "="*70)
    print(" [DW LOAD] INICIANDO CARGA DIMENSIONAL EN POSTGRESQL (music_dw)")
    print("="*70)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 1. Limpieza idempotente de tablas
        print(" -> Reiniciando tablas del modelo dimensional...")
        cursor.execute("""
            TRUNCATE TABLE fact_music_performance, dim_track, dim_artist, dim_genre, dim_grammy_award 
            RESTART IDENTITY CASCADE;
        """)

        # 2. Poblar dim_track
        print(" -> Cargando dim_track...")
        tracks_df = df_integrated[['track_id', 'track_name', 'album_name', 'explicit']].drop_duplicates(subset=['track_id'])
        for _, row in tracks_df.iterrows():
            t_name = safe_str(row['track_name'], 500, default='Sin Título')
            a_name = safe_str(row['album_name'], 500, default='Sin Álbum')
            
            cursor.execute("""
                INSERT INTO dim_track (track_id, track_name, album_name, explicit)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (track_id) DO NOTHING;
            """, (
                safe_str(row['track_id'], 100),
                t_name,
                a_name,
                bool(row['explicit']) if pd.notnull(row['explicit']) else False
            ))
            
        # 3. Poblar dim_artist
        print(" -> Cargando dim_artist...")
        artists = df_integrated['artists'].dropna().unique()
        for artist in artists:
            a_str = safe_str(artist, 500, default='Artista Desconocido')
            cursor.execute("""
                INSERT INTO dim_artist (artist_name)
                VALUES (%s)
                ON CONFLICT (artist_name) DO NOTHING;
            """, (a_str,))
            
        # 4. Poblar dim_genre
        print(" -> Cargando dim_genre...")
        genres = df_integrated['track_genre'].dropna().unique()
        for genre in genres:
            g_str = safe_str(genre, 100, default='Desconocido')
            cursor.execute("""
                INSERT INTO dim_genre (genre_name)
                VALUES (%s)
                ON CONFLICT (genre_name) DO NOTHING;
            """, (g_str,))

        # 5. Poblar dim_grammy_award
        print(" -> Cargando dim_grammy_award...")
        grammy_df = df_integrated[df_integrated['year'].notnull()][['year', 'category', 'nominee', 'winner']].drop_duplicates()
        for _, row in grammy_df.iterrows():
            cursor.execute("""
                INSERT INTO dim_grammy_award (year, category, nominee, winner)
                VALUES (%s, %s, %s, %s);
            """, (
                int(row['year']),
                safe_str(row['category'], 500, default='Sin Categoría'),
                safe_str(row['nominee'], 500, default='Sin Nominado'),
                bool(row['winner']) if pd.notnull(row['winner']) else False
            ))
            
        conn.commit()
        
        # 6. Mapeo de Claves Sustitutas y Carga de fact_music_performance
        print(" -> Resolviendo Surrogate Keys para fact_music_performance...")
        
        track_map = pd.read_sql_query("SELECT track_key, track_id FROM dim_track;", conn).set_index('track_id')['track_key'].to_dict()
        artist_map = pd.read_sql_query("SELECT artist_key, artist_name FROM dim_artist;", conn).set_index('artist_name')['artist_key'].to_dict()
        genre_map = pd.read_sql_query("SELECT genre_key, genre_name FROM dim_genre;", conn).set_index('genre_name')['genre_key'].to_dict()
        
        grammy_db = pd.read_sql_query("SELECT grammy_key, year, category, nominee FROM dim_grammy_award;", conn)
        grammy_map = grammy_db.set_index(['year', 'category', 'nominee'])['grammy_key'].to_dict()
        
        print(" -> Insertando registros en fact_music_performance...")
        fact_rows = []
        for _, row in df_integrated.iterrows():
            t_key = track_map.get(safe_str(row['track_id'], 100))
            a_key = artist_map.get(safe_str(row['artists'], 500, default='Artista Desconocido'))
            g_key = genre_map.get(safe_str(row['track_genre'], 100, default='Desconocido'))
            
            gr_key = None
            if pd.notnull(row['year']):
                gr_key = grammy_map.get((
                    int(row['year']),
                    safe_str(row['category'], 500, default='Sin Categoría'),
                    safe_str(row['nominee'], 500, default='Sin Nominado')
                ))

            if t_key and a_key and g_key:
                fact_rows.append((
                    t_key, a_key, g_key, gr_key,
                    int(row['popularity']) if pd.notnull(row['popularity']) else None,
                    int(row['duration_ms']) if pd.notnull(row['duration_ms']) else None,
                    float(row['danceability']) if pd.notnull(row['danceability']) else None,
                    float(row['energy']) if pd.notnull(row['energy']) else None,
                    int(row['key']) if pd.notnull(row['key']) else None,
                    float(row['loudness']) if pd.notnull(row['loudness']) else None,
                    int(row['mode']) if pd.notnull(row['mode']) else None,
                    float(row['speechiness']) if pd.notnull(row['speechiness']) else None,
                    float(row['acousticness']) if pd.notnull(row['acousticness']) else None,
                    float(row['instrumentalness']) if pd.notnull(row['instrumentalness']) else None,
                    float(row['liveness']) if pd.notnull(row['liveness']) else None,
                    float(row['valence']) if pd.notnull(row['valence']) else None,
                    float(row['tempo']) if pd.notnull(row['tempo']) else None,
                    int(row['is_grammy_nominated']),
                    int(row['is_grammy_winner'])
                ))
                
        cursor.executemany("""
            INSERT INTO fact_music_performance (
                track_key, artist_key, genre_key, grammy_key,
                popularity, duration_ms, danceability, energy, key,
                loudness, mode, speechiness, acousticness, instrumentalness,
                liveness, valence, tempo, is_grammy_nominated, is_grammy_winner
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, fact_rows)

        conn.commit()
        print(f"✅ [DW LOAD COMPLETO] Insertados {len(fact_rows):,} registros en fact_music_performance.")
        return True

    except Exception as e:
        conn.rollback()
        print(f"❌ [DW LOAD ERROR] Fallo durante la carga al Data Warehouse: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_dw_metrics():
    """Consulta métricas clave en PostgreSQL para comparar ejecuciones."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM dim_track) AS tracks_count,
            (SELECT COUNT(*) FROM dim_artist) AS artists_count,
            (SELECT COUNT(*) FROM fact_music_performance) AS fact_count,
            (SELECT COALESCE(SUM(popularity), 0) FROM fact_music_performance) AS sum_popularity,
            (SELECT COALESCE(ROUND(AVG(duration_ms)::numeric, 2), 0) FROM fact_music_performance) AS avg_duration
    """)
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    return {
        "dim_track": res[0],
        "dim_artist": res[1],
        "fact_rows": res[2],
        "sum_popularity": res[3],
        "avg_duration": float(res[4])
    }

if __name__ == "__main__":
    from transform import transform_spotify_data, transform_grammy_data, integrate_datasets
    from validate_prepared import validate_prepared_data
    
    # 1. Preparación de datos
    df_sp_raw = pd.read_csv("data/raw/spotify_dataset.csv")
    df_sp_clean = transform_spotify_data(df_sp_raw)
    
    conn = connect_db()
    df_gr_raw = pd.read_sql_query("SELECT * FROM raw_grammys;", conn)
    conn.close()
    
    df_gr_clean = transform_grammy_data(df_gr_raw)
    df_integrated = integrate_datasets(df_sp_clean, df_gr_clean)
    
    if validate_prepared_data(df_integrated):
        print("\n" + "="*70)
        print(" [TEST 7.3] EJECUTANDO PRUEBA DE REPETIBILIDAD E IDEMPOTENCIA (SAFE RERUN)")
        print("="*70)
        
        # Ejecución 1: Carga Inicial
        print("\n--- RUN 1: CARGA INICIAL ---")
        load_data_warehouse(df_integrated)
        metrics_run1 = get_dw_metrics()
        
        # Ejecución 2: Re-ejecución del mismo lote (Rerun)
        print("\n--- RUN 2: RE-EJECUCIÓN DEL MISMO LOTE (RERUN) ---")
        load_data_warehouse(df_integrated)
        metrics_run2 = get_dw_metrics()
        
        # Comparación y Verificación
        print("\n" + "="*70)
        print(" [EVIDENCIA 7.3] COMPARACIÓN DE MÉTRICAS ANTES Y DESPUÉS DEL RERUN")
        print("="*70)
        print(f" -> Filas dim_track           : Run 1 = {metrics_run1['dim_track']:,} | Run 2 = {metrics_run2['dim_track']:,}")
        print(f" -> Filas dim_artist          : Run 1 = {metrics_run1['dim_artist']:,} | Run 2 = {metrics_run2['dim_artist']:,}")
        print(f" -> Filas fact_performance    : Run 1 = {metrics_run1['fact_rows']:,} | Run 2 = {metrics_run2['fact_rows']:,}")
        print(f" -> Suma Popularidad          : Run 1 = {metrics_run1['sum_popularity']:,} | Run 2 = {metrics_run2['sum_popularity']:,}")
        print(f" -> Promedio Duración (ms)    : Run 1 = {metrics_run1['avg_duration']:,} | Run 2 = {metrics_run2['avg_duration']:,}")
        
        is_idempotent = (metrics_run1 == metrics_run2)
        if is_idempotent:
            print("\n✅ [PRUEBA EXITOSA] Idempotencia verificada: 0% de duplicación silenciosa.")
        else:
            print("\n❌ [PRUEBA FALLIDA] Se detectó duplicación de registros.")