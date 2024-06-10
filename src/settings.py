# Import standard library modules
from pathlib import Path

# The ROOT_DIR should represent the absolute path of the project root folder
ROOT_DIR = Path(__file__).absolute().parent.parent

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "02-raw"
PROCESSED_DIR = DATA_DIR / "03-processed"
OUTPUT_DIR = DATA_DIR / "04-output"
GIS_DIR = DATA_DIR / "05-gis"

PROJ_CRS = "EPSG:4326"
METRIC_CRS = "EPSG:3857"

CLIMATE_VARIABLES_LIST = [
    "CO",
    "HI",
    "NDVI",
    "NO2",
    "O3",
    "PM10",
    "PM25",
    "PNP",
    "PR",
    "RH",
    "SO2",
    "SPI3",
    "SPI6",
    "SR",
    "Tave",
    "Tmax",
    "Tmin",
    "UVR",
    "WS",
]
