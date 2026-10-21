"""
Tests de integracion para el esquema y pipeline del Data Warehouse.
Usa una base de datos temporal para no contaminar datos de produccion.
"""
import pytest
from sqlalchemy import text
from src.database.schema import init_database
from src.pipeline.seed_data import seed_sample_data, FARMACOS, REACCIONES, CASES


@pytest.fixture(scope="module")
def test_db(tmp_path_factory):
    """Crea una DB SQLite temporal con datos de prueba completos."""
    db_path = tmp_path_factory.mktemp("db") / "test_radar.db"
    seed_sample_data(db_path=db_path)
    return init_database(db_path)


class TestDatabaseSchema:
    def test_todas_las_tablas_existen(self, test_db):
        with test_db.connect() as conn:
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        tablas = {r[0] for r in result}
        esperadas = {
            "dim_farmaco", "dim_reaccion", "dim_regulacion_peru",
            "dim_tiempo", "fact_senales_riesgo", "fact_evidencia_texto",
        }
        assert esperadas.issubset(tablas), f"Tablas faltantes: {esperadas - tablas}"

    def test_indices_de_optimizacion_existen(self, test_db):
        with test_db.connect() as conn:
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='index'")
            ).fetchall()
        indices = {r[0] for r in result}
        assert "idx_senales_farmaco" in indices
        assert "idx_senales_riesgo" in indices
        assert "idx_evidencia_farmaco" in indices

    def test_unique_constraint_en_fact_senales(self, test_db):
        """Insertar un par duplicado debe fallar silenciosamente (INSERT OR IGNORE)."""
        with test_db.connect() as conn:
            antes = conn.execute(
                text("SELECT COUNT(*) FROM fact_senales_riesgo")
            ).scalar()
            # Intentar re-insertar mismas claves -> debe ignorarse
            f_id = conn.execute(
                text("SELECT farmaco_id FROM dim_farmaco WHERE principio_activo='VALPROATO DE SODIO'")
            ).scalar()
            r_id = conn.execute(
                text("SELECT reaccion_id FROM dim_reaccion WHERE termino_preferido='Malformaciones congenitas'")
            ).scalar()
            t_id = conn.execute(
                text("SELECT tiempo_id FROM dim_tiempo LIMIT 1")
            ).scalar()
            conn.execute(
                text("INSERT OR IGNORE INTO fact_senales_riesgo "
                     "(farmaco_id,reaccion_id,tiempo_id,casos_farmaco_reaccion,casos_farmaco_otras_reac,"
                     "casos_otros_farmacos_reac,casos_otros_farmacos_otras_reac,prr,nivel_riesgo) "
                     "VALUES (:f,:r,:t,100,200,300,400,2.5,'Alto')"),
                {"f": f_id, "r": r_id, "t": t_id},
            )
            despues = conn.execute(
                text("SELECT COUNT(*) FROM fact_senales_riesgo")
            ).scalar()
        assert antes == despues  # No debe haber aumentado


class TestSeedData:
    def test_cantidad_farmacos_correcta(self, test_db):
        with test_db.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM dim_farmaco")).scalar()
        assert count == len(FARMACOS)

    def test_cantidad_pares_de_riesgo_correcta(self, test_db):
        with test_db.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM fact_senales_riesgo")).scalar()
        assert count == len(CASES)

    def test_cantidad_reacciones_correcta(self, test_db):
        with test_db.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM dim_reaccion")).scalar()
        assert count == len(REACCIONES)

    def test_regulacion_peru_cargada(self, test_db):
        with test_db.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM dim_regulacion_peru")).scalar()
        assert count >= 7

    def test_evidencias_texto_cargadas(self, test_db):
        with test_db.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM fact_evidencia_texto")).scalar()
        assert count >= 6

    def test_periodo_faers_existe(self, test_db):
        with test_db.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dim_tiempo WHERE periodo_etiqueta='2024-Q2'")
            ).fetchone()
        assert row is not None

    def test_niveles_riesgo_son_validos(self, test_db):
        with test_db.connect() as conn:
            niveles = conn.execute(
                text("SELECT DISTINCT nivel_riesgo FROM fact_senales_riesgo")
            ).fetchall()
        valores = {r[0] for r in niveles}
        assert valores.issubset({"Alto", "Medio", "Bajo"})

    def test_prr_siempre_mayor_que_cero(self, test_db):
        with test_db.connect() as conn:
            min_prr = conn.execute(
                text("SELECT MIN(prr) FROM fact_senales_riesgo")
            ).scalar()
        assert min_prr > 0

    def test_max_prr_es_razonable(self, test_db):
        """El PRR maximo debe ser < 1000 (valores documentados en literatura)."""
        with test_db.connect() as conn:
            max_prr = conn.execute(
                text("SELECT MAX(prr) FROM fact_senales_riesgo")
            ).scalar()
        assert max_prr < 1000


class TestIntegrationQueries:
    def test_join_principal_del_dashboard(self, test_db):
        """Verifica que el JOIN principal del dashboard retorna datos correctos."""
        query = """
        SELECT f.principio_activo, r.termino_preferido, s.prr, s.nivel_riesgo
        FROM fact_senales_riesgo s
        JOIN dim_farmaco f ON s.farmaco_id = f.farmaco_id
        JOIN dim_reaccion r ON s.reaccion_id = r.reaccion_id
        LEFT JOIN dim_regulacion_peru reg ON f.principio_activo = reg.principio_activo
        ORDER BY s.prr DESC
        """
        with test_db.connect() as conn:
            rows = conn.execute(text(query)).fetchall()
        assert len(rows) == len(CASES)
        # Primer registro debe tener el PRR mas alto
        assert rows[0][2] >= rows[-1][2]

    def test_valproato_malformaciones_es_alto_riesgo(self, test_db):
        with test_db.connect() as conn:
            row = conn.execute(text("""
                SELECT s.nivel_riesgo, s.prr
                FROM fact_senales_riesgo s
                JOIN dim_farmaco f ON s.farmaco_id = f.farmaco_id
                JOIN dim_reaccion r ON s.reaccion_id = r.reaccion_id
                WHERE f.principio_activo = 'VALPROATO DE SODIO'
                  AND r.termino_preferido = 'Malformaciones congenitas'
            """)).fetchone()
        assert row is not None
        assert row[0] == "Alto"
        assert row[1] > 2.0

    def test_metformina_nauseas_es_bajo_riesgo(self, test_db):
        with test_db.connect() as conn:
            row = conn.execute(text("""
                SELECT s.nivel_riesgo
                FROM fact_senales_riesgo s
                JOIN dim_farmaco f ON s.farmaco_id = f.farmaco_id
                JOIN dim_reaccion r ON s.reaccion_id = r.reaccion_id
                WHERE f.principio_activo = 'METFORMINA'
                  AND r.termino_preferido = 'Nauseas leves'
            """)).fetchone()
        assert row is not None
        assert row[0] == "Bajo"

    def test_clozapina_agranulocitosis_es_alto_riesgo(self, test_db):
        with test_db.connect() as conn:
            row = conn.execute(text("""
                SELECT s.nivel_riesgo, s.prr
                FROM fact_senales_riesgo s
                JOIN dim_farmaco f ON s.farmaco_id = f.farmaco_id
                JOIN dim_reaccion r ON s.reaccion_id = r.reaccion_id
                WHERE f.principio_activo = 'CLOZAPINA'
                  AND r.termino_preferido = 'Agranulocitosis'
            """)).fetchone()
        assert row is not None
        assert row[0] == "Alto"
        assert row[1] > 2.0

    def test_fenilbutazona_no_vigente(self, test_db):
        with test_db.connect() as conn:
            row = conn.execute(text("""
                SELECT reg.registro_sanitario_vigente
                FROM dim_regulacion_peru reg
                WHERE reg.principio_activo = 'FENILBUTAZONA'
            """)).fetchone()
        assert row is not None
        assert row[0] == 0  # No vigente

    def test_valproato_vigente_en_pnume(self, test_db):
        with test_db.connect() as conn:
            row = conn.execute(text("""
                SELECT reg.registro_sanitario_vigente, reg.incluido_pnume
                FROM dim_regulacion_peru reg
                WHERE reg.principio_activo = 'VALPROATO DE SODIO'
            """)).fetchone()
        assert row is not None
        assert row[0] == 1  # Vigente
        assert row[1] == 1  # En PNUME

    def test_evidencias_valproato_existen(self, test_db):
        with test_db.connect() as conn:
            rows = conn.execute(text("""
                SELECT e.contenido_extraido
                FROM fact_evidencia_texto e
                JOIN dim_farmaco f ON e.farmaco_id = f.farmaco_id
                WHERE f.principio_activo = 'VALPROATO DE SODIO'
            """)).fetchall()
        assert len(rows) >= 2

    def test_ordenado_por_prr_desc(self, test_db):
        """El PRR debe estar ordenado de mayor a menor en el ranking."""
        with test_db.connect() as conn:
            prrs = conn.execute(
                text("SELECT prr FROM fact_senales_riesgo ORDER BY prr DESC")
            ).fetchall()
        valores = [r[0] for r in prrs]
        assert valores == sorted(valores, reverse=True)
