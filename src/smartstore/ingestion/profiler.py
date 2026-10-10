from pathlib  import Path
import pandas as pd

def profile_csv(csv_path: Path) -> dict:
    """
    Genera un perfil básico de un archivo CSV.

    Args:
        csv_path (Path): Ruta del archivo CSV que se va a inspeccionar.

    Returns:
        dict: Diccionario con información sobre el archivo, incluyendo
        su nombre, tamaño, cantidad de filas y columnas, nombres y tipos
        de columnas, valores faltantes y filas completamente duplicadas.
    """
    df = pd.read_csv(csv_path)

    profile = {
        "file_size_bytes": csv_path.stat().st_size,
        "file_name": csv_path.name,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "data_types": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isna().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
    }

    return profile

def profile_directory(data_dir: Path) -> list[dict]:
    """
    Genera perfiles de todos los archivos CSV de una carpeta.

    Args:
        data_dir (Path): Ruta de la carpeta que contiene los archivos CSV.

    Returns:
        list[dict]: Lista de diccionarios, donde cada diccionario contiene
        el perfil de un archivo CSV encontrado en la carpeta.
    """
    csv_files = sorted(data_dir.glob("*.csv"))

    profiles = []

    for csv_file in csv_files:
        profile = profile_csv(csv_file)
        profiles.append(profile)

    return profiles
