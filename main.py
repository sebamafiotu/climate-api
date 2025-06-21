from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from geopy.geocoders import Nominatim
import rasterio
from rasterio.transform import rowcol
import numpy as np

app = FastAPI(
    title="Köppen-Geiger Climate API",
    description="Returns Köppen-Geiger climate classification based on coordinates or city name.",
    version="1.0"
)

TIF_PATH = "koppen_geiger_0p00833333.tif"

KOPPEN_CLASSES = {
    1: "Af - Tropical rainforest",
    2: "Am - Tropical monsoon",
    3: "Aw - Tropical savanna",
    31: "As - Tropical savanna (summer dry)",
    4: "BWh - Hot desert",
    5: "BWk - Cold desert",
    6: "BSh - Hot semi-arid",
    7: "BSk - Cold semi-arid",
    8: "Csa - Hot-summer Mediterranean",
    9: "Csb - Warm-summer Mediterranean",
    10: "Csc - Cold-summer Mediterranean",
    11: "Cwa - Humid subtropical (dry winter)",
    12: "Cwb - Subtropical highland",
    13: "Cwc - Cold subtropical highland",
    14: "Cfa - Humid subtropical",
    15: "Cfb - Oceanic",
    16: "Cfc - Subpolar oceanic",
    17: "Dsa - Hot-summer continental (dry summer)",
    18: "Dsb - Warm-summer continental (dry summer)",
    19: "Dsc - Subarctic (dry summer)",
    20: "Dsd - Very cold dry-summer continental",
    21: "Dwa - Hot-summer continental (dry winter)",
    22: "Dwb - Warm-summer continental (dry winter)",
    23: "Dwc - Subarctic (dry winter)",
    24: "Dwd - Very cold dry-winter subarctic",
    25: "Dfa - Hot-summer continental",
    26: "Dfb - Warm-summer continental",
    27: "Dfc - Subarctic",
    28: "Dfd - Extremely cold subarctic",
    29: "ET - Tundra",
    30: "EF - Ice cap"
}

geolocator = Nominatim(user_agent="climate-api")

def get_climate_data(lat: float, lon: float):
    with rasterio.open(TIF_PATH) as src:
        row, col = rowcol(src.transform, lon, lat)
        value = src.read(1)[row, col]

    class_code = int(value)
    description = KOPPEN_CLASSES.get(class_code, "Unknown")

    return {
        "latitude": lat,
        "longitude": lon,
        "class_code": class_code,
        "climate": description
    }

@app.get("/")
def root():
    return {"message": "Köppen-Geiger Climate API is running."}

@app.get("/climate")
def get_climate(lat: float = Query(None), lon: float = Query(None), city: str = Query(None)):
    try:
        if city:
            location = geolocator.geocode(city)
            if not location:
                return JSONResponse(status_code=404, content={"error": "City not found"})
            data = get_climate_data(location.latitude, location.longitude)
        elif lat is not None and lon is not None:
            data = get_climate_data(lat, lon)
        else:
            return JSONResponse(status_code=400, content={"error": "You must provide 'lat' and 'lon' or 'city'."})
        return data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/climate/types")
def get_all_climate_types():
    return {"koppen_classes": KOPPEN_CLASSES}

@app.get("/climate/codes")
def get_used_codes():
    try:
        with rasterio.open(TIF_PATH) as src:
            data = src.read(1)
            unique_classes = list(np.unique(data))
        used = {
            int(code): KOPPEN_CLASSES.get(int(code), "Unknown")
            for code in unique_classes
        }
        return {"used_classes": used}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
