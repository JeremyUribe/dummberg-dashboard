import os
import time
import pandas as pd
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# =====================================================
# CONFIGURACIÓN
# =====================================================
URL = "https://www.sbs.gob.pe/app/pp/vectorprecios/n_vector_precios"

DOWNLOAD_DIR = r"C:\Users\jerja\OneDrive\Escritorio\SBS_Vector\downloads"
OUTPUT_PICKLE = r"C:\Users\jerja\OneDrive\Escritorio\SBS_Vector\vector_precios_unido_pen.pkl"

FECHA_OBJETIVO = datetime(2026, 10, 20)


COD_MONEDA = "1"  # PEN
MONEDA = "PEN"
EMISOR_OBJETIVO = "GOB.CENTRAL"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ============================  =========================
# SELENIUM
# ==================================
# ===================
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--start-maximized")
chrome_options.add_experimental_option(
    "prefs",
    {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True,
    },
)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)
wait = WebDriverWait(driver, 10)

# =====================================================
# FUNCIONES
# =====================================================
def limpiar_descargas():
    for f in os.listdir(DOWNLOAD_DIR):
        try:
            os.remove(os.path.join(DOWNLOAD_DIR, f))
        except:
            pass

def esperar_descarga(timeout=15):
    for _ in range(timeout):
        files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith((".xls", ".xlsx"))]
        if files:
            return files[0]
        time.sleep(0.3)
    return None

def cerrar_popup():
    try:
        btn = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
        if btn.is_displayed():
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.2)
    except:
        pass

# =====================================================
# SCRAPING DE UNA FECHA
# =====================================================
driver.get(URL)
time.sleep(2)

fecha_str = FECHA_OBJETIVO.strftime("%d/%m/%Y")
print(f"📅 Actualizando fecha: {fecha_str}")

data_nueva = []

try:
    limpiar_descargas()

    # Fecha
    input_fecha = wait.until(
        EC.presence_of_element_located((By.ID, "txtFiltroFechaProceso"))
    )
    driver.execute_script(
        "arguments[0].value=arguments[1]; arguments[0].dispatchEvent(new Event('change')); arguments[0].dispatchEvent(new Event('blur'));",
        input_fecha,
        fecha_str
    )
    time.sleep(0.2)

    # Moneda
    select_moneda = Select(driver.find_element(By.ID, "cboFiltroTipoMoneda"))
    select_moneda.select_by_value(COD_MONEDA)
    time.sleep(0.2)

    cerrar_popup()

    # Consultar
    btn = driver.find_element(By.ID, "btnBuscarInformacion")
    driver.execute_script("arguments[0].click();", btn)

    try:
        wait.until(EC.presence_of_element_located((By.ID, "tblVectorPrecios")))
        time.sleep(0.5)
    except:
        print("⏭️ Sin datos para esa fecha")
        driver.quit()
        exit()

    # Exportar
    btn_excel = driver.find_element(By.XPATH, "//button[contains(., 'Listado')]")
    driver.execute_script("arguments[0].click();", btn_excel)

    archivo = esperar_descarga()

    if not archivo:
        print("⏭️ No se descargó archivo")
        driver.quit()
        exit()

    df = pd.read_excel(os.path.join(DOWNLOAD_DIR, archivo))
    df.columns = [c.lower() for c in df.columns]

    # Filtro emisor
    df = df[df["emisor"] == EMISOR_OBJETIVO]

    if df.empty:
        print("⏭️ Sin GOB.CENTRAL")
        driver.quit()
        exit()

    df["fecha"] = FECHA_OBJETIVO
    df["moneda_consulta"] = MONEDA

    data_nueva.append(df)
    print(f"✅ {len(df)} filas descargadas")

except Exception as e:
    print(f"⚠️ Error: {e}")

driver.quit()

# =====================================================
# ACTUALIZAR PICKLE
# =====================================================
if not data_nueva:
    print("⚠️ No hay data nueva, pickle intacto")
    exit()

df_nuevo = pd.concat(data_nueva, ignore_index=True)

if os.path.exists(OUTPUT_PICKLE):
    df_hist = pd.read_pickle(OUTPUT_PICKLE)
    df_hist["fecha"] = pd.to_datetime(df_hist["fecha"])

    # Eliminar esa fecha si ya existía
    df_hist = df_hist[df_hist["fecha"].dt.date != FECHA_OBJETIVO.date()]

    df_final = pd.concat([df_hist, df_nuevo], ignore_index=True)
else:
    df_final = df_nuevo

df_final.to_pickle(OUTPUT_PICKLE)

print("\n🎉 FECHA ACTUALIZADA CORRECTAMENTE")
print(f"📦 Total registros: {len(df_final):,}")
