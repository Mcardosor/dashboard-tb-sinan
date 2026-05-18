"""
baixar_geojson.py
-----------------
Baixa o GeoJSON dos estados brasileiros, normaliza as propriedades
e salva em dados_dashboard/br_states.geojson.

Execute UMA VEZ na sua máquina (que tem internet) e depois commit o arquivo:
    python baixar_geojson.py
    git add dados_dashboard/br_states.geojson
    git commit -m "feat: adiciona GeoJSON dos estados brasileiros"
    git push

O app.py vai carregar esse arquivo do disco — sem dependência de URLs externas.
"""

import json
from pathlib import Path
import requests

SAIDA = Path("dados_dashboard/br_states.geojson")

# Mapeamento: código IBGE numérico → sigla UF
# Usado para normalizar o GeoJSON da IBGE (que usa codarea = "35", "33", etc.)
IBGE_PARA_SIGLA = {
    "12": "AC", "27": "AL", "16": "AP", "13": "AM", "29": "BA", "23": "CE",
    "53": "DF", "32": "ES", "52": "GO", "21": "MA", "51": "MT", "50": "MS",
    "31": "MG", "15": "PA", "25": "PB", "41": "PR", "26": "PE", "22": "PI",
    "33": "RJ", "24": "RN", "43": "RS", "11": "RO", "14": "RR", "42": "SC",
    "35": "SP", "28": "SE", "17": "TO",
}

# Mapeamento: nome completo → sigla (para GeoJSON que usa properties.name)
NOME_PARA_SIGLA = {
    "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM",
    "Bahia": "BA", "Ceará": "CE", "Distrito Federal": "DF", "Espírito Santo": "ES",
    "Goiás": "GO", "Maranhão": "MA", "Mato Grosso": "MT", "Mato Grosso do Sul": "MS",
    "Minas Gerais": "MG", "Pará": "PA", "Paraíba": "PB", "Paraná": "PR",
    "Pernambuco": "PE", "Piauí": "PI", "Rio de Janeiro": "RJ",
    "Rio Grande do Norte": "RN", "Rio Grande do Sul": "RS", "Rondônia": "RO",
    "Roraima": "RR", "Santa Catarina": "SC", "São Paulo": "SP",
    "Sergipe": "SE", "Tocantins": "TO",
}

URLS = [
    # codeforgermany/click_that_hood — usa properties.name = nome completo em português
    # Ex: "São Paulo", "Rio de Janeiro". Mesma fonte usada no dashboard-tuberculose principal.
    (
        "codeforgermany/click_that_hood",
        "https://raw.githubusercontent.com/codeforgermany/"
        "click_that_hood/main/public/data/brazil-states.geojson",
    ),
    # IBGE Malhas — endpoint correto para ESTADOS individualmente (27 features separadas)
    # paises/BR retorna o contorno do país inteiro — não serve para choropleth por estado
    (
        "IBGE Malhas — estados",
        "https://servicodados.ibge.gov.br/api/v3/malhas/estados"
        "?formato=application/vnd.geo+json&qualidade=minima",
    ),
    # giuliano-macedo — usa properties.id = sigla (AC, AL, AM...)
    (
        "giuliano-macedo/geodata-br-states",
        "https://raw.githubusercontent.com/giuliano-macedo/"
        "geodata-br-states/main/geojson/br_states.geojson",
    ),
]


def normalizar_geojson(geo: dict, nome_fonte: str) -> dict:
    """
    Garante que cada feature tenha properties.sigla (ex: "SP", "RJ").
    Detecta automaticamente o campo identificador usado pela fonte.
    """
    for feature in geo["features"]:
        props = feature["properties"]

        # Já tem sigla correta? (giuliano-macedo com properties.id)
        if "id" in props and props["id"] in NOME_PARA_SIGLA.values():
            props["sigla"] = props["id"]

        # Tem código IBGE numérico? (IBGE Malhas)
        elif "codarea" in props:
            props["sigla"] = IBGE_PARA_SIGLA.get(str(props["codarea"]), "")

        # Tem nome completo? (click_that_hood)
        elif "name" in props:
            props["sigla"] = NOME_PARA_SIGLA.get(props["name"], "")

        elif "nome" in props:
            props["sigla"] = NOME_PARA_SIGLA.get(props["nome"], "")

    siglas_ok = sum(1 for f in geo["features"] if f["properties"].get("sigla"))
    print(f"  Siglas mapeadas: {siglas_ok}/{len(geo['features'])} estados")
    return geo


def baixar() -> None:
    SAIDA.parent.mkdir(exist_ok=True)

    for nome, url in URLS:
        print(f"\nTentando {nome}...")
        print(f"  URL: {url[:70]}...")
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            geo = r.json()

            if geo.get("type") != "FeatureCollection" or not geo.get("features"):
                print("  ❌ Resposta não é um GeoJSON válido")
                continue

            print(f"  ✅ {len(geo['features'])} features recebidas")
            props_exemplo = list(geo["features"][0]["properties"].keys())
            print(f"  Propriedades: {props_exemplo}")

            geo = normalizar_geojson(geo, nome)

            SAIDA.write_text(json.dumps(geo, ensure_ascii=False), encoding="utf-8")
            tamanho = SAIDA.stat().st_size / 1024
            print(f"\n✅ Salvo em {SAIDA} ({tamanho:.0f} KB)")
            print("\nPróximos passos:")
            print("  git add dados_dashboard/br_states.geojson")
            print('  git commit -m "feat: adiciona GeoJSON dos estados brasileiros"')
            print("  git push")
            return

        except requests.exceptions.JSONDecodeError:
            print("  ❌ Resposta não é JSON (URL pode estar redirecionando)")
        except Exception as e:
            print(f"  ❌ Erro: {type(e).__name__}: {e}")

    print("\n❌ Nenhuma URL funcionou. Verifique sua conexão com a internet.")


if __name__ == "__main__":
    baixar()
