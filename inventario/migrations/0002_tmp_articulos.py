from django.db import migrations

def create_tmp_table(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == 'postgresql':
        schema_editor.execute("""
            CREATE UNLOGGED TABLE IF NOT EXISTS tmp_articulos (
              id_carga BIGINT,
              sku VARCHAR(64),
              codigo_bodega VARCHAR(20),
              codigo_zona VARCHAR(20),
              cantidad INT,
              lote VARCHAR(64),
              precio_costo_real NUMERIC(10,2),
              fecha_fabricacion DATE,
              fecha_vencimiento DATE,
              numero_serie VARCHAR(100)
            );
        """)
    else:
        # SQLite u otro: tabla normal
        schema_editor.execute("""
            CREATE TABLE IF NOT EXISTS tmp_articulos (
              id_carga BIGINT,
              sku VARCHAR(64),
              codigo_bodega VARCHAR(20),
              codigo_zona VARCHAR(20),
              cantidad INT,
              lote VARCHAR(64),
              precio_costo_real NUMERIC(10,2),
              fecha_fabricacion DATE,
              fecha_vencimiento DATE,
              numero_serie VARCHAR(100)
            );
        """)
    schema_editor.execute("CREATE INDEX IF NOT EXISTS idx_tmp_articulos_carga ON tmp_articulos(id_carga);")

def drop_tmp_table(apps, schema_editor):
    schema_editor.execute("DROP TABLE IF EXISTS tmp_articulos;")

class Migration(migrations.Migration):
    dependencies = [
        ('inventario', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(create_tmp_table, reverse_code=drop_tmp_table)
    ]
