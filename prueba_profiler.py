from pathlib import Path

from smartstore.ingestion.profiler import profile_directory

ruta_datos = Path("data/raw")

resultados = profile_directory(ruta_datos)

print(f"Archivos analizados: {len(resultados)}")

for resultado in resultados:
    print(
        f"{resultado['file_name']}: "
        f"{resultado['rows']} filas, "
        f"{resultado['columns']} columnas"
    )