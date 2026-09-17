"""
extractor_camara.py
Módulo de extracción y procesamiento de datos abiertos de la Cámara de Diputadas y Diputados de Chile.
Fuente oficial: https://opendata.camara.cl/camaradiputados/WServices/WSLegislativo.asmx
"""

import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import requests

BASE_URL = "https://opendata.camara.cl/camaradiputados/WServices/WSLegislativo.asmx"
NAMESPACES = {"ns": "http://opendata.camara.cl/camaradiputados/v1"}


def obtener_detalle_votacion(votacion_id: int) -> Dict:
    """
    Obtiene el detalle nominal de una votación específica por su ID.
    Retorna un diccionario con metadatos de la votación y la lista individual de votos.
    """
    url = f"{BASE_URL}/retornarVotacionDetalle?prmVotacionId={votacion_id}"
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Error] No se pudo consultar la votación {votacion_id}: {e}", file=sys.stderr)
        return {}

    root = ET.fromstring(response.content)

    # Metadatos generales
    descripcion = root.findtext("ns:Descripcion", default="", namespaces=NAMESPACES)
    fecha = root.findtext("ns:Fecha", default="", namespaces=NAMESPACES)
    resultado = root.findtext("ns:Resultado", default="", namespaces=NAMESPACES)
    total_si = root.findtext("ns:TotalSi", default="0", namespaces=NAMESPACES)
    total_no = root.findtext("ns:TotalNo", default="0", namespaces=NAMESPACES)
    total_abstencion = root.findtext("ns:TotalAbstencion", default="0", namespaces=NAMESPACES)

    # Detalle de votos nominales
    votos = []
    for nodo_voto in root.findall(".//ns:Voto", NAMESPACES):
        diputado = nodo_voto.find("ns:Diputado", NAMESPACES)
        dip_id = diputado.findtext("ns:Id", default="", namespaces=NAMESPACES) if diputado is not None else ""
        nombre = diputado.findtext("ns:Nombre", default="", namespaces=NAMESPACES) if diputado is not None else ""
        apellido_pat = diputado.findtext("ns:ApellidoPaterno", default="", namespaces=NAMESPACES) if diputado is not None else ""
        apellido_mat = diputado.findtext("ns:ApellidoMaterno", default="", namespaces=NAMESPACES) if diputado is not None else ""
        
        opcion_elem = nodo_voto.find("ns:OpcionVoto", NAMESPACES)
        opcion = opcion_elem.text if opcion_elem is not None and opcion_elem.text else ""

        votos.append({
            "diputado_id": dip_id,
            "nombre_completo": f"{nombre} {apellido_pat} {apellido_mat}".strip(),
            "opcion": opcion.strip()
        })

    return {
        "votacion_id": votacion_id,
        "descripcion": descripcion.strip(),
        "fecha": fecha.strip(),
        "resultado": resultado.strip(),
        "totales_oficiales": {
            "si": int(total_si) if total_si.isdigit() else 0,
            "no": int(total_no) if total_no.isdigit() else 0,
            "abstencion": int(total_abstencion) if total_abstencion.isdigit() else 0,
        },
        "total_votos_registrados": len(votos),
        "votos": votos
    }


def obtener_votaciones_anno(anno: int) -> List[Dict]:
    """
    Obtiene la lista de votaciones registradas en la Cámara para un año determinado.
    """
    url = f"{BASE_URL}/retornarVotacionesXAnno?prmAnno={anno}"
    try:
        response = requests.get(url, timeout=25)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Error] No se pudieron obtener votaciones para el año {anno}: {e}", file=sys.stderr)
        return []

    root = ET.fromstring(response.content)
    lista = []
    for nodo in root.findall(".//ns:Votacion", NAMESPACES):
        v_id = nodo.findtext("ns:Id", default="", namespaces=NAMESPACES)
        desc = nodo.findtext("ns:Descripcion", default="", namespaces=NAMESPACES)
        fecha = nodo.findtext("ns:Fecha", default="", namespaces=NAMESPACES)
        tipo = nodo.findtext("ns:Tipo", default="", namespaces=NAMESPACES)
        resultado = nodo.findtext("ns:Resultado", default="", namespaces=NAMESPACES)

        if v_id:
            lista.append({
                "id": int(v_id),
                "descripcion": desc.strip(),
                "fecha": fecha.strip(),
                "tipo": tipo.strip(),
                "resultado": resultado.strip()
            })

    return lista


def resumen_conteo_votos(detalle: Dict) -> Dict[str, int]:
    """
    Cuenta el total de votos por cada opción (Afirmativo, En Contra, Abstención, Dispensado, etc.).
    """
    conteo = {}
    for v in detalle.get("votos", []):
        op = v.get("opcion", "DESCONOCIDO")
        conteo[op] = conteo.get(op, 0) + 1
    return conteo


if __name__ == "__main__":
    print("=== Political Sentinel: Extractor de Datos Abiertos (Cámara de Diputadas y Diputados) ===")
    
    anno_test = 2024
    print(f"\n--> Consultando lista de votaciones para el año {anno_test}...")
    votaciones = obtener_votaciones_anno(anno_test)
    print(f"Total de votaciones registradas en {anno_test}: {len(votaciones)}")
    
    if votaciones:
        muestra = votaciones[0]  # Tomamos la primera de la lista
        v_id = muestra["id"]
        print(f"\n--> Consultando detalle nominal de la votación ID={v_id}: '{muestra['descripcion'][:80]}'...")
        detalle = obtener_detalle_votacion(v_id)
        
        print(f"Fecha: {detalle['fecha']} | Resultado Oficial: {detalle['resultado']}")
        print(f"Totales Oficiales: {detalle['totales_oficiales']}")
        
        conteo = resumen_conteo_votos(detalle)
        print("\nDesglose de opciones en el detalle:")
        for op, cant in conteo.items():
            print(f"  - {op}: {cant}")
            
        print(f"\nMuestra de los primeros 5 diputados y su voto:")
        for v in detalle.get("votos", [])[:5]:
            print(f"  • {v['nombre_completo']}: [{v['opcion']}]")

