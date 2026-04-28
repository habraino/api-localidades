from fastapi import FastAPI, HTTPException, status, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from database import get_db, init_db
from localidades_data import (
    LOCALIDADES_AGRUPADAS, 
    DISTRITOS_OFICIAIS,
    get_localidades_por_distrito,
    get_distrito_por_localidade,
    get_all_localidades,
    get_estatisticas
)
import crud

app = FastAPI(
    title="API Gestão de Localidades - São Tomé e Príncipe",
    description="API para gestão de distritos e localidades de São Tomé e Príncipe",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Inicializar banco de dados
init_db()

# Schemas Pydantic
class LugarBase(BaseModel):
    nome: str

class LugarCreate(LugarBase):
    distrito_nome: str

class LugarResponse(LugarBase):
    id: int
    distrito_id: int

class LugarDetailResponse(LugarBase):
    id: int
    distrito_id: int
    distrito_nome: str

class DistritoBase(BaseModel):
    nome: str

class DistritoResponse(DistritoBase):
    id: int
    lugares: List[LugarResponse] = []

class LocalidadeInfo(BaseModel):
    nome: str
    distrito: str

class SearchResult(BaseModel):
    query: str
    total: int
    resultados: List[LugarDetailResponse]

class EstatisticasResponse(BaseModel):
    total_distritos: int
    total_localidades: int
    localidades_por_distrito: Dict[str, int]
    distrito_com_mais_localidades: str
    distrito_com_menos_localidades: str

# ----- Endpoints da API -----

@app.get("/")
def root():
    """Endpoint raiz com informações da API"""
    return {
        "nome": "API Gestão de Localidades",
        "pais": "São Tomé e Príncipe",
        "versao": "2.0.0",
        "endpoints": {
            "distritos": "/distritos",
            "localidades": "/localidades",
            "buscar": "/buscar?q=texto",
            "estatisticas": "/estatisticas",
            "docs": "/docs"
        }
    }

@app.post("/carregar_dados_iniciais", response_model=Dict[str, Any])
def carregar_dados_iniciais():
    """Carrega todos os dados agrupados para o banco de dados"""
    with get_db() as conn:
        inseridos = 0
        duplicados = 0
        
        for distrito_nome, localidades in LOCALIDADES_AGRUPADAS.items():
            # Obter ou criar distrito
            distrito = crud.get_or_create_distrito(conn, distrito_nome)
            
            for localidade in localidades:
                # Verificar se o lugar já existe
                lugar_existente = crud.get_lugar_by_nome_distrito(conn, localidade, distrito['id'])
                if not lugar_existente:
                    crud.create_lugar(conn, localidade, distrito['id'])
                    inseridos += 1
                else:
                    duplicados += 1
        
        return {
            "mensagem": "Dados carregados com sucesso",
            "inseridos": inseridos,
            "duplicados": duplicados,
            "total_distritos": len(DISTRITOS_OFICIAIS),
            "total_localidades": sum(len(locs) for locs in LOCALIDADES_AGRUPADAS.values())
        }

@app.get("/distritos", response_model=List[str])
def listar_distritos():
    """Lista todos os distritos oficiais de São Tomé e Príncipe"""
    return DISTRITOS_OFICIAIS

@app.get("/distritos/{distrito_nome}/localidades", response_model=List[str])
def listar_localidades_por_distrito(distrito_nome: str):
    """Lista todas as localidades de um distrito específico"""
    # Normalizar nome
    distrito_normalizado = distrito_nome.strip()
    
    # Buscar distrito correto
    distrito_encontrado = None
    for distrito in DISTRITOS_OFICIAIS:
        if distrito.lower() == distrito_normalizado.lower():
            distrito_encontrado = distrito
            break
    
    if not distrito_encontrado:
        raise HTTPException(
            status_code=404, 
            detail=f"Distrito '{distrito_nome}' não encontrado. Distritos disponíveis: {DISTRITOS_OFICIAIS}"
        )
    
    localidades = get_localidades_por_distrito(distrito_encontrado)
    return localidades

@app.get("/localidades", response_model=Dict[str, List[str]])
def listar_todas_localidades_agrupadas():
    """Lista todas as localidades agrupadas por distrito"""
    return get_all_localidades()

@app.get("/localidades/todas", response_model=List[str])
def listar_todas_localidades_flat():
    """Lista todas as localidades em uma única lista"""
    todas = []
    for localidades in LOCALIDADES_AGRUPADAS.values():
        todas.extend(localidades)
    return sorted(todas)

@app.get("/localidades/buscar")
def buscar_localidade_por_nome(
    nome: str = Query(..., description="Nome da localidade para buscar", min_length=1)
):
    """Busca uma localidade e retorna seu distrito"""
    nome_busca = nome.strip()
    
    # Busca exata
    distrito = get_distrito_por_localidade(nome_busca)
    if distrito:
        return {
            "tipo": "exata",
            "localidade": nome_busca,
            "distrito": distrito
        }
    
    # Busca parcial (case insensitive)
    resultados = []
    nome_busca_lower = nome_busca.lower()
    
    for distrito_nome, localidades in LOCALIDADES_AGRUPADAS.items():
        for localidade in localidades:
            if nome_busca_lower in localidade.lower():
                resultados.append({
                    "localidade": localidade,
                    "distrito": distrito_nome
                })
    
    if resultados:
        return {
            "tipo": "parcial",
            "query": nome_busca,
            "total": len(resultados),
            "resultados": resultados[:20]  # Limitar a 20 resultados
        }
    
    raise HTTPException(
        status_code=404, 
        detail=f"Localidade '{nome_busca}' não encontrada"
    )

@app.get("/localidades/{nome_localidade}/distrito")
def obter_distrito_da_localidade(nome_localidade: str):
    """Obtém o distrito de uma localidade específica"""
    distrito = get_distrito_por_localidade(nome_localidade)
    if not distrito:
        raise HTTPException(
            status_code=404, 
            detail=f"Localidade '{nome_localidade}' não encontrada"
        )
    
    return {
        "localidade": nome_localidade,
        "distrito": distrito
    }

@app.get("/estatisticas", response_model=EstatisticasResponse)
def estatisticas_localidades():
    """Retorna estatísticas detalhadas das localidades por distrito"""
    stats = get_estatisticas()
    total_localidades = sum(stats.values())
    
    distrito_mais = max(stats, key=stats.get)
    distrito_menos = min(stats, key=stats.get)
    
    # Buscar dados do banco
    with get_db() as conn:
        db_stats = crud.get_total_count(conn)
    
    return EstatisticasResponse(
        total_distritos=len(DISTRITOS_OFICIAIS),
        total_localidades=total_localidades,
        localidades_por_distrito=stats,
        distrito_com_mais_localidades=distrito_mais,
        distrito_com_menos_localidades=distrito_menos
    )

@app.get("/buscar", response_model=SearchResult)
def buscar_lugares(
    q: str = Query(..., description="Termo de busca", min_length=1),
    limit: int = Query(50, description="Limite de resultados", ge=1, le=100)
):
    """Busca lugares por nome (case insensitive) no banco de dados"""
    with get_db() as conn:
        resultados = crud.search_lugares(conn, q)
        
        # Aplicar limite
        if len(resultados) > limit:
            resultados = resultados[:limit]
        
        return SearchResult(
            query=q,
            total=len(resultados),
            resultados=resultados
        )

# ----- Endpoints do Banco de Dados (CRUD) -----

@app.get("/db/distritos", response_model=List[DistritoResponse])
def listar_distritos_db():
    """Lista todos os distritos do banco de dados com seus lugares"""
    with get_db() as conn:
        return crud.get_all_distritos_with_lugares(conn)

@app.get("/db/lugares", response_model=List[LugarDetailResponse])
def listar_todos_lugares_db():
    """Lista todos os lugares do banco de dados"""
    with get_db() as conn:
        return crud.get_all_lugares(conn)

@app.post("/db/lugares", response_model=LugarResponse, status_code=status.HTTP_201_CREATED)
def criar_lugar_db(lugar: LugarCreate):
    """Cria um novo lugar no banco de dados"""
    with get_db() as conn:
        # Verificar se o distrito existe
        distrito = crud.get_distrito_by_nome(conn, lugar.distrito_nome)
        if not distrito:
            # Verificar se é um distrito oficial
            if lugar.distrito_nome not in DISTRITOS_OFICIAIS:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Distrito '{lugar.distrito_nome}' não encontrado. Distritos disponíveis: {DISTRITOS_OFICIAIS}"
                )
            # Criar distrito
            distrito = crud.get_or_create_distrito(conn, lugar.distrito_nome)
        
        # Verificar duplicado
        existente = crud.get_lugar_by_nome_distrito(conn, lugar.nome, distrito['id'])
        if existente:
            raise HTTPException(
                status_code=400, 
                detail=f"Lugar '{lugar.nome}' já existe no distrito '{lugar.distrito_nome}'"
            )
        
        novo_lugar = crud.create_lugar(conn, lugar.nome, distrito['id'])
        return novo_lugar

@app.delete("/db/lugares/{lugar_id}")
def remover_lugar_db(lugar_id: int):
    """Remove um lugar do banco de dados pelo ID"""
    with get_db() as conn:
        removido = crud.delete_lugar(conn, lugar_id)
        if not removido:
            raise HTTPException(status_code=404, detail="Lugar não encontrado")
        return {"mensagem": "Lugar removido com sucesso", "id": lugar_id}

@app.get("/db/stats")
def estatisticas_db():
    """Retorna estatísticas do banco de dados"""
    with get_db() as conn:
        return crud.get_total_count(conn)

# ----- Health Check -----
@app.get("/health")
def health_check():
    """Verifica se a API está funcionando"""
    return {"status": "ok", "versao": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 API Gestão de Localidades - São Tomé e Príncipe")
    print("=" * 60)
    print(f"📊 Distritos: {len(DISTRITOS_OFICIAIS)}")
    print(f"📍 Localidades: {sum(len(locs) for locs in LOCALIDADES_AGRUPADAS.values())}")
    print("=" * 60)
    print(f"📚 Documentação: http://localhost:8000/docs")
    print(f"🔧 Redoc: http://localhost:8000/redoc")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)