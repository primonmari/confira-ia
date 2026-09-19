
import json
import re
import unicodedata
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# CONFIGURAÇÕES
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "gemma2:2b"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# ============================================================
# CARREGAMENTO DOS ARQUIVOS
# ============================================================

def carregar_json(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)

    except (FileNotFoundError, json.JSONDecodeError) as erro:
        st.error(f"Erro ao carregar {caminho}: {erro}")
        return []


def carregar_jsonl(caminho):
    dados = []

    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:

            for linha in arquivo:

                linha = linha.strip()

                if not linha:
                    continue

                try:
                    dados.append(
                        json.loads(linha)
                    )

                except json.JSONDecodeError:
                    continue

    except FileNotFoundError:
        st.error(
            f"Arquivo não encontrado: {caminho}"
        )

    return dados


golpes = carregar_json(
    DATA_DIR / "golpes.json"
)

sinais_alerta = carregar_json(
    DATA_DIR / "sinais_alerta.json"
)

orientacoes = carregar_json(
    DATA_DIR / "orientacoes.json"
)

faq = carregar_json(
    DATA_DIR / "faq.json"
)

produtos_financeiros = carregar_json(
    DATA_DIR / "produtos_financeiros.json"
)

fraudes_india = carregar_jsonl(
    DATA_DIR / "INDIA-SPECIFIC-FRAUD-V1.jsonl"
)


# IMPORTANTE:
# casos_teste NÃO é utilizado como contexto para a IA.
# Ele é utilizado apenas como base de avaliação.

casos_teste = carregar_json(
    DATA_DIR / "casos_teste.json"
)


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar(texto):

    if texto is None:
        return ""

    texto = str(texto).lower()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


# ============================================================
# CONVERSÃO GENÉRICA DE REGISTROS PARA TEXTO
# ============================================================

def valor_para_texto(valor):

    if valor is None:
        return ""

    if isinstance(valor, dict):

        partes = []

        for chave, valor_item in valor.items():

            partes.append(
                f"{chave}: "
                f"{valor_para_texto(valor_item)}"
            )

        return " ".join(partes)

    if isinstance(valor, list):

        return " ".join(
            valor_para_texto(item)
            for item in valor
        )

    return str(valor)


def registro_para_texto(registro):

    return normalizar(
        valor_para_texto(registro)
    )


# ============================================================
# EXTRAÇÃO DE TERMOS
# ============================================================

def extrair_termos(texto):

    texto = normalizar(texto)

    return set(
        palavra
        for palavra in re.findall(
            r"\b[\w]+\b",
            texto
        )
        if len(palavra) >= 3
    )


# ============================================================
# BUSCA DE REGISTROS RELEVANTES
# ============================================================

def pontuar_relevancia(
    situacao,
    registro
):

    texto_situacao = normalizar(
        situacao
    )

    texto_registro = registro_para_texto(
        registro
    )

    if (
        not texto_situacao
        or not texto_registro
    ):
        return 0

    termos_situacao = extrair_termos(
        texto_situacao
    )

    termos_registro = extrair_termos(
        texto_registro
    )

    if (
        not termos_situacao
        or not termos_registro
    ):
        return 0

    intersecao = (
        termos_situacao
        .intersection(
            termos_registro
        )
    )

    return len(intersecao)


def buscar_registros(
    situacao,
    dados,
    limite=3
):

    resultados = []

    for registro in dados:

        pontuacao = pontuar_relevancia(
            situacao,
            registro
        )

        if pontuacao > 0:

            resultados.append(
                (
                    pontuacao,
                    registro
                )
            )

    resultados.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        registro
        for _, registro
        in resultados[:limite]
    ]


# ============================================================
# IDENTIFICAÇÃO DOS SINAIS DE ALERTA
# ============================================================

def obter_indicadores(sinal):

    """
    Localiza os indicadores existentes em cada registro
    de sinais_alerta.json sem depender de uma estrutura
    fixa de campos.
    """

    indicadores = []

    if not isinstance(
        sinal,
        dict
    ):
        return indicadores

    for chave, valor in sinal.items():

        chave_normalizada = normalizar(
            chave
        )

        if "indicador" not in chave_normalizada:
            continue

        if isinstance(
            valor,
            list
        ):

            indicadores.extend(
                str(item)
                for item in valor
                if item is not None
            )

        elif isinstance(
            valor,
            str
        ):

            indicadores.append(
                valor
            )

    return indicadores


def obter_nome_sinal(sinal):

    if not isinstance(
        sinal,
        dict
    ):
        return "Sinal de alerta"

    for chave in (
        "nome",
        "titulo",
        "sinal",
        "tipo",
        "descricao"
    ):

        if (
            chave in sinal
            and sinal[chave]
        ):

            return str(
                sinal[chave]
            )

    return "Sinal de alerta"


def obter_peso_sinal(sinal):

    if not isinstance(
        sinal,
        dict
    ):
        return 0

    peso = sinal.get(
        "peso",
        0
    )

    try:

        return float(
            peso
        )

    except (
        TypeError,
        ValueError
    ):

        return 0


def indicador_encontrado(
    indicador,
    situacao
):

    indicador = normalizar(
        indicador
    )

    situacao = normalizar(
        situacao
    )

    if not indicador:
        return False

    # --------------------------------------------------------
    # Frases completas são verificadas primeiro.
    # --------------------------------------------------------

    if indicador in situacao:
        return True

    # --------------------------------------------------------
    # Para indicadores maiores, tenta encontrar seus termos.
    # --------------------------------------------------------

    termos = [
        termo
        for termo in re.findall(
            r"\b[\w]+\b",
            indicador
        )
        if len(termo) >= 3
    ]

    if not termos:
        return False

    # --------------------------------------------------------
    # Evita considerar um sinal presente somente porque
    # uma palavra genérica apareceu isoladamente.
    # --------------------------------------------------------

    encontrados = sum(
        1
        for termo in termos
        if termo in situacao
    )

    if len(termos) == 1:

        return encontrados == 1

    proporcao = (
        encontrados
        / len(termos)
    )

    return proporcao >= 0.5


def identificar_sinais(situacao):

    sinais_encontrados = []

    for sinal in sinais_alerta:

        indicadores = obter_indicadores(
            sinal
        )

        encontrados = []

        for indicador in indicadores:

            if indicador_encontrado(
                indicador,
                situacao
            ):

                encontrados.append(
                    indicador
                )

        if encontrados:

            sinais_encontrados.append(
                {
                    "nome": obter_nome_sinal(
                        sinal
                    ),

                    "peso": obter_peso_sinal(
                        sinal
                    ),

                    "indicadores_encontrados":
                        encontrados,

                    "descricao":
                        sinal.get(
                            "descricao",
                            ""
                        )
                        if isinstance(
                            sinal,
                            dict
                        )
                        else ""
                }
            )

    return sinais_encontrados


# ============================================================
# CÁLCULO DE RISCO
# ============================================================

def calcular_risco(sinais):

    peso_total = sum(
        sinal["peso"]
        for sinal in sinais
    )

    # --------------------------------------------------------
    # Não existe mais risco indeterminado.
    #
    # Nenhum sinal ou peso de até 2:
    # BAIXO
    #
    # Peso de 3 até 5:
    # MÉDIO
    #
    # Peso acima de 5:
    # ALTO
    # --------------------------------------------------------

    if peso_total > 5:

        return (
            "alto",
            peso_total
        )

    if peso_total >= 3:

        return (
            "medio",
            peso_total
        )

    return (
        "baixo",
        peso_total
    )


# ============================================================
# SITUAÇÃO CONCRETA
# ============================================================

def identificar_situacao_concreta(
    situacao
):

    texto = normalizar(
        situacao
    )

    if len(texto) < 15:
        return False

    # --------------------------------------------------------
    # Sinais concretos já encontrados na base.
    # --------------------------------------------------------

    sinais = identificar_sinais(
        situacao
    )

    if sinais:
        return True

    # --------------------------------------------------------
    # Ações ou acontecimentos descritos pelo usuário.
    # --------------------------------------------------------

    padroes = [

        r"\brecebi\b",

        r"\bmandaram\b",

        r"\bpediram\b",

        r"\bsolicitaram\b",

        r"\bcliquei\b",

        r"\bclicaram\b",

        r"\benviaram\b",

        r"\bligaram\b",

        r"\bligacao\b",

        r"\bmensagem\b",

        r"\blink\b",

        r"\bdisseram\b",

        r"\bdisse\b",

        r"\baconteceu\b",

        r"\bapareceu\b",

        r"\btransferi\b",

        r"\bpaguei\b",

        r"\binformei\b",

        r"\bpedindo\b",

        r"\bsolicitando\b"
    ]

    return any(
        re.search(
            padrao,
            texto
        )
        for padrao in padroes
    )


# ============================================================
# BUSCAS COMPLEMENTARES
# ============================================================

def buscar_golpes(
    situacao
):

    return buscar_registros(
        situacao,
        golpes,
        limite=3
    )


def buscar_orientacoes(
    situacao
):

    return buscar_registros(
        situacao,
        orientacoes,
        limite=4
    )


def buscar_faq(
    situacao
):

    return buscar_registros(
        situacao,
        faq,
        limite=3
    )


def buscar_produtos(
    situacao
):

    return buscar_registros(
        situacao,
        produtos_financeiros,
        limite=3
    )


def buscar_fraudes_india(
    situacao
):

    return buscar_registros(
        situacao,
        fraudes_india,
        limite=2
    )


# ============================================================
# CONTEXTO
# ============================================================

def criar_contexto(
    situacao
):

    sinais = identificar_sinais(
        situacao
    )

    risco, peso_total = calcular_risco(
        sinais
    )

    return {

        "situacao_concreta":
            identificar_situacao_concreta(
                situacao
            ),

        "risco_deterministico":
            risco,

        "peso_total":
            peso_total,

        "sinais_identificados":
            sinais,

        "golpes_relacionados":
            buscar_golpes(
                situacao
            ),

        "orientacoes_preventivas":
            buscar_orientacoes(
                situacao
            ),

        "faq_relevante":
            buscar_faq(
                situacao
            ),

        "produtos_financeiros":
            buscar_produtos(
                situacao
            ),

        "fraudes_relacionadas":
            buscar_fraudes_india(
                situacao
            )
    }


# ============================================================
# FORMATAÇÃO DO CONTEXTO PARA A IA
# ============================================================

def formatar_lista(dados):

    if not dados:

        return (
            "Nenhum registro relevante "
            "encontrado."
        )

    partes = []

    for item in dados:

        partes.append(
            valor_para_texto(
                item
            )
        )

    return "\n".join(
        f"- {item}"
        for item in partes
    )


def formatar_sinais(
    sinais
):

    if not sinais:

        return (
            "Nenhum sinal de alerta "
            "identificado."
        )

    partes = []

    for sinal in sinais:

        indicadores = ", ".join(
            sinal[
                "indicadores_encontrados"
            ]
        )

        partes.append(
            f"- {sinal['nome']} "
            f"(peso: {sinal['peso']}, "
            f"indicadores encontrados: "
            f"{indicadores})"
        )

    return "\n".join(
        partes
    )


# ============================================================
# PROMPT
# ============================================================

PROMPT_SISTEMA = """
Você é o Confira IA, um assistente especializado na
identificação de possíveis golpes e fraudes financeiras
e digitais.

Sua função é analisar situações relatadas pelo usuário
com base no contexto fornecido pela aplicação.

REGRAS IMPORTANTES:

1. Não declare que uma situação é definitivamente um golpe.

2. Não invente sinais de alerta.

3. Os sinais identificados pela aplicação são a referência
   principal para a análise.

4. Não transforme palavras isoladas e genéricas em sinais
   de alerta.

5. Não solicite senhas, códigos de autenticação, dados
   bancários completos ou outras informações sensíveis.

6. Não forneça instruções para contornar mecanismos de
   segurança.

7. Quando houver sinais concretos, explique por que eles
   são relevantes.

8. Quando não houver sinais de alerta identificados,
   classifique a situação como risco baixo.

9. Utilize as orientações recuperadas da base de conhecimento
   como apoio.

10. Não trate registros semelhantes como prova de fraude.

11. O campo "risco" deve respeitar o risco calculado pela
    camada determinística da aplicação.

12. Não altere os sinais identificados pela aplicação.

13. O sistema possui somente três níveis de risco:
    baixo, medio e alto.

14. Nunca utilize "indeterminado" como valor para o campo
    "risco".

Responda SOMENTE em JSON válido, no seguinte formato:

{
  "risco": "baixo",
  "explicacao": "Explicação objetiva.",
  "sinais": [],
  "orientacoes": [],
  "precisa_esclarecimento": false,
  "pergunta_esclarecimento": ""
}
"""


# ============================================================
# CHAMADA AO OLLAMA
# ============================================================

def chamar_ollama(
    prompt
):

    try:

        resposta = requests.post(

            OLLAMA_URL,

            json={

                "model":
                    MODELO,

                "prompt":
                    prompt,

                "system":
                    PROMPT_SISTEMA,

                "stream":
                    False,

                "options": {

                    "temperature":
                        0.1
                }
            },

            timeout=120
        )

        resposta.raise_for_status()

        dados = resposta.json()

        return dados.get(
            "response",
            ""
        )

    except requests.RequestException as erro:

        return json.dumps(
            {
                "erro":
                    "Não foi possível consultar "
                    f"o modelo: {erro}"
            },
            ensure_ascii=False
        )


# ============================================================
# EXTRAÇÃO DO JSON DA RESPOSTA
# ============================================================

def extrair_json(
    texto
):

    texto = texto.strip()

    try:

        return json.loads(
            texto
        )

    except json.JSONDecodeError:

        pass

    inicio = texto.find(
        "{"
    )

    fim = texto.rfind(
        "}"
    )

    if (
        inicio == -1
        or fim == -1
    ):

        return None

    trecho = texto[
        inicio:fim + 1
    ]

    try:

        return json.loads(
            trecho
        )

    except json.JSONDecodeError:

        return None


# ============================================================
# VALIDAÇÃO DA RESPOSTA DA IA
# ============================================================

def validar_resposta(
    resposta_ia,
    contexto
):

    risco = contexto[
        "risco_deterministico"
    ]

    sinais = contexto[
        "sinais_identificados"
    ]

    if not isinstance(
        resposta_ia,
        dict
    ):

        resposta_ia = {}

    # --------------------------------------------------------
    # O risco calculado pela aplicação prevalece.
    # --------------------------------------------------------

    resposta_ia[
        "risco"
    ] = risco

    # --------------------------------------------------------
    # Os sinais identificados pela aplicação prevalecem.
    # --------------------------------------------------------

    resposta_ia[
        "sinais"
    ] = [

        sinal["nome"]

        for sinal in sinais
    ]

    # --------------------------------------------------------
    # Explicação padrão.
    # --------------------------------------------------------

    if not resposta_ia.get(
        "explicacao"
    ):

        if sinais:

            resposta_ia[
                "explicacao"
            ] = (
                "A situação apresenta sinais de alerta "
                "compatíveis com padrões conhecidos de "
                "golpes."
            )

        else:

            resposta_ia[
                "explicacao"
            ] = (
                "Não foram identificados sinais de alerta "
                "relevantes na situação relatada."
            )

    # --------------------------------------------------------
    # Orientações.
    # --------------------------------------------------------

    if not isinstance(
        resposta_ia.get(
            "orientacoes"
        ),
        list
    ):

        resposta_ia[
            "orientacoes"
        ] = []

    if not resposta_ia[
        "orientacoes"
    ]:

        orientacoes_base = contexto[
            "orientacoes_preventivas"
        ]

        resposta_ia[
            "orientacoes"
        ] = [

            valor_para_texto(
                item
            )

            for item
            in orientacoes_base[:3]
        ]

    # --------------------------------------------------------
    # Não existe mais esclarecimento obrigatório.
    # --------------------------------------------------------

    resposta_ia[
        "precisa_esclarecimento"
    ] = False

    resposta_ia[
        "pergunta_esclarecimento"
    ] = ""

    return resposta_ia


# ============================================================
# ANÁLISE PRINCIPAL
# ============================================================

def analisar_situacao(
    situacao
):

    contexto = criar_contexto(
        situacao
    )

    # ========================================================
    # CONTEXTO PARA A IA
    # ========================================================

    contexto_prompt = f"""
SITUAÇÃO RELATADA:
{situacao}

RISCO CALCULADO PELA APLICAÇÃO:
{contexto["risco_deterministico"]}

PESO TOTAL DOS SINAIS:
{contexto["peso_total"]}

SINAIS DE ALERTA IDENTIFICADOS:
{formatar_sinais(
    contexto["sinais_identificados"]
)}

PADRÕES DE GOLPES RELACIONADOS:
{formatar_lista(
    contexto["golpes_relacionados"]
)}

ORIENTAÇÕES PREVENTIVAS:
{formatar_lista(
    contexto["orientacoes_preventivas"]
)}

FAQ RELACIONADO:
{formatar_lista(
    contexto["faq_relevante"]
)}

PRODUTOS FINANCEIROS RELACIONADOS:
{formatar_lista(
    contexto["produtos_financeiros"]
)}

REFERÊNCIAS INTERNACIONAIS:
{formatar_lista(
    contexto["fraudes_relacionadas"]
)}
"""

    resposta_bruta = chamar_ollama(
        contexto_prompt
    )

    resposta_ia = extrair_json(
        resposta_bruta
    )

    resposta_final = validar_resposta(
        resposta_ia,
        contexto
    )

    return resposta_final


# ============================================================
# INTERFACE
# ============================================================

st.set_page_config(

    page_title="Confira IA",

    page_icon="🛡️",

    layout="centered"
)


# ============================================================
# ESTADO DA CONVERSA
# ============================================================

if "mensagens" not in st.session_state:

    st.session_state.mensagens = []


# ============================================================
# CABEÇALHO
# ============================================================

st.title(
    "🛡️ Confira IA"
)

st.write(
    "Assistente de identificação de possíveis golpes "
    "e fraudes financeiras e digitais."
)


# ============================================================
# MENSAGEM INICIAL
# ============================================================

if not st.session_state.mensagens:

    with st.chat_message(
        "assistant"
    ):

        st.write(
            "Olá! Eu sou o Confira IA. Envie uma mensagem "
            "ou descreva uma situação suspeita e vou ajudar "
            "você a identificar possíveis sinais de golpe."
        )


# ============================================================
# HISTÓRICO
# ============================================================

for mensagem in st.session_state.mensagens:

    if mensagem[
        "tipo"
    ] == "usuario":

        with st.chat_message(
            "user"
        ):

            st.write(
                mensagem[
                    "conteudo"
                ]
            )

    else:

        with st.chat_message(
            "assistant"
        ):

            resultado = mensagem[
                "resultado"
            ]

            risco = resultado.get(
                "risco",
                "baixo"
            )

            explicacao = resultado.get(
                "explicacao",
                ""
            )

            sinais = resultado.get(
                "sinais",
                []
            )

            orientacoes = resultado.get(
                "orientacoes",
                []
            )


            # ------------------------------------------------
            # EXPLICAÇÃO
            # ------------------------------------------------

            if explicacao:

                st.write(
                    explicacao
                )


            # ------------------------------------------------
            # RISCO
            # ------------------------------------------------

            if risco == "alto":

                st.markdown(
                    "**🚨 RISCO: ALTO**"
                )

            elif risco == "medio":

                st.markdown(
                    "**🟡 RISCO: MÉDIO**"
                )

            else:

                st.markdown(
                    "**🟢 RISCO: BAIXO**"
                )


            # ------------------------------------------------
            # SINAIS DE ALERTA
            # ------------------------------------------------

            if sinais:

                st.write(
                    "**Sinais de alerta:**"
                )

                for sinal in sinais:

                    st.write(
                        f"- {sinal}"
                    )


            # ------------------------------------------------
            # ORIENTAÇÕES
            # ------------------------------------------------

            if orientacoes:

                st.write(
                    "**Orientações preventivas:**"
                )

                for orientacao in orientacoes:

                    st.write(
                        f"- {orientacao}"
                    )


# ============================================================
# ENTRADA DO USUÁRIO
# ============================================================

situacao = st.chat_input(
    "Descreva uma situação ou faça uma pergunta..."
)


# ============================================================
# NOVA MENSAGEM
# ============================================================

if situacao:

    st.session_state.mensagens.append(

        {
            "tipo":
                "usuario",

            "conteudo":
                situacao
        }
    )

    with st.spinner(
        "Analisando a situação..."
    ):

        resultado = analisar_situacao(
            situacao
        )

    st.session_state.mensagens.append(

        {
            "tipo":
                "assistente",

            "resultado":
                resultado
        }
    )

    st.rerun()
