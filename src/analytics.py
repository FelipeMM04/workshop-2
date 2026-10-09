import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

OUTPUT_DIR = "data/metadata/charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_connection():
    # Conexión al PostgreSQL que está corriendo en tu contenedor 'workshop-2'
    return psycopg2.connect(
        dbname="music_dw",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )

def generate_analytics():
    print("\n" + "="*70)
    print(" [8.1 ANALYTICS] CONSULTANDO DATA WAREHOUSE EN DOCKER (workshop-2)")
    print("="*70)
    
    conn = get_connection()
    
    # ------------------------------------------------------------------
    # 1. KPI 1: Top 10 Géneros por Popularidad Promedio
    # ------------------------------------------------------------------
    query1 = """
        SELECT 
            g.genre_name,
            ROUND(AVG(f.popularity)::numeric, 2) AS avg_popularity
        FROM fact_music_performance f
        JOIN dim_genre g ON f.genre_key = g.genre_key
        GROUP BY g.genre_name
        ORDER BY avg_popularity DESC
        LIMIT 10;
    """
    df1 = pd.read_sql_query(query1, conn)
    print("\n[CONSULTA 1: TOP GÉNEROS]")
    print(df1)

    plt.figure(figsize=(10, 5))
    sns.barplot(data=df1, x='avg_popularity', y='genre_name', palette='Blues_r')
    plt.title('KPI 1: Top 10 Géneros Musicales por Popularidad Promedio', fontsize=12, fontweight='bold')
    plt.xlabel('Popularidad Promedio (0-100)')
    plt.ylabel('Género')
    plt.tight_layout()
    chart1_path = f"{OUTPUT_DIR}/kpi1_top_genres.png"
    plt.savefig(chart1_path)
    plt.close()
    print(f" -> Guardada imagen: {chart1_path}")

    # ------------------------------------------------------------------
    # 2. KPI 2: Impacto del Estatus Grammy en la Popularidad
    # ------------------------------------------------------------------
    query2 = """
        SELECT 
            CASE 
                WHEN f.is_grammy_winner = 1 THEN 'Ganador Grammy'
                WHEN f.is_grammy_nominated = 1 THEN 'Nominado Grammy'
                ELSE 'Sin Nominación'
            END AS status_grammy,
            ROUND(AVG(f.popularity)::numeric, 2) AS avg_popularity
        FROM fact_music_performance f
        GROUP BY status_grammy
        ORDER BY avg_popularity DESC;
    """
    df2 = pd.read_sql_query(query2, conn)
    print("\n[CONSULTA 2: ESTATUS GRAMMY]")
    print(df2)

    plt.figure(figsize=(8, 5))
    sns.barplot(data=df2, x='status_grammy', y='avg_popularity', palette='viridis')
    plt.title('KPI 2: Comparación de Popularidad según Estatus Grammy', fontsize=12, fontweight='bold')
    plt.xlabel('Estatus de Premiación')
    plt.ylabel('Popularidad Promedio')
    plt.tight_layout()
    chart2_path = f"{OUTPUT_DIR}/kpi2_grammy_impact.png"
    plt.savefig(chart2_path)
    plt.close()
    print(f" -> Guardada imagen: {chart2_path}")

    # ------------------------------------------------------------------
    # 3. KPI 3: Top 10 Artistas Más Populares
    # ------------------------------------------------------------------
    query3 = """
        SELECT 
            a.artist_name,
            ROUND(AVG(f.popularity)::numeric, 2) AS avg_popularity
        FROM fact_music_performance f
        JOIN dim_artist a ON f.artist_key = a.artist_key
        WHERE a.artist_name != 'Artista Desconocido'
        GROUP BY a.artist_name
        HAVING COUNT(f.track_key) >= 5
        ORDER BY avg_popularity DESC
        LIMIT 10;
    """
    df3 = pd.read_sql_query(query3, conn)
    print("\n[CONSULTA 3: TOP ARTISTAS]")
    print(df3)

    plt.figure(figsize=(10, 5))
    sns.barplot(data=df3, x='avg_popularity', y='artist_name', palette='magma')
    plt.title('KPI 3: Top 10 Artistas por Popularidad Promedio (min. 5 canciones)', fontsize=12, fontweight='bold')
    plt.xlabel('Popularidad Promedio')
    plt.ylabel('Artista')
    plt.tight_layout()
    chart3_path = f"{OUTPUT_DIR}/kpi3_top_artists.png"
    plt.savefig(chart3_path)
    plt.close()
    print(f" -> Guardada imagen: {chart3_path}")

    conn.close()
    print("\n✅ [ÉXITO] Consultas ejecutadas y visualizaciones guardadas correctamente.")

if __name__ == "__main__":
    generate_analytics()