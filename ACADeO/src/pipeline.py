"""
Pipeline MVP para análise e comparação de apólices D&O.

Comandos:
    python pipeline.py --demo
    python pipeline.py "apolice_1.pdf"
    python pipeline.py "apolice_1.pdf" "apolice_2.pdf"
    python pipeline.py --listar
    python pipeline.py --comparar 1 2
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

MAX_BYTES = 20 * 1024 * 1024
BANCO_PADRAO = "vectorbase/apolices.db"

MIME = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

SCHEMA = {
    "type": "object",
    "properties": {
        "seguradora": {"type": "string"},
        "tomador": {"type": "string"},
        "processo_susep": {"type": "string"},
        "tipo_documento": {"type": "string"},
        "vigencia_inicio": {"type": "string"},
        "vigencia_fim": {"type": "string"},
        "base_reclamacoes": {"type": "string"},
        "lmi_texto": {"type": "string"},
        "lmi_valor": {"type": "number"},
        "limite_agregado_texto": {"type": "string"},
        "limite_agregado_valor": {"type": "number"},
        "premio_texto": {"type": "string"},
        "premio_valor": {"type": "number"},
        "pos_franquia": {"type": "string"},
        "cobertura_a": {"type": "string"},
        "cobertura_b": {"type": "string"},
        "cobertura_c": {"type": "string"},
        "custos_defesa_em_adicao": {"type": "string"},
        "prazo_complementar": {"type": "string"},
        "prazo_suplementar": {"type": "string"},
        "retroatividade": {"type": "string"},
        "territorialidade": {"type": "string"},
        "exclusoes": {
            "type": "array",
            "items": {"type": "string"},
        },
        "evidencias": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "campo": {"type": "string"},
                    "pagina": {"type": "integer"},
                    "trecho": {"type": "string"},
                },
                "required": ["campo", "pagina", "trecho"],
            },
        },
    },
    "required": [
        "seguradora",
        "tomador",
        "processo_susep",
        "tipo_documento",
        "vigencia_inicio",
        "vigencia_fim",
        "base_reclamacoes",
        "lmi_texto",
        "limite_agregado_texto",
        "premio_texto",
        "pos_franquia",
        "cobertura_a",
        "cobertura_b",
        "cobertura_c",
        "custos_defesa_em_adicao",
        "prazo_complementar",
        "prazo_suplementar",
        "retroatividade",
        "territorialidade",
        "exclusoes",
        "evidencias",
    ],
}

PROMPT = """
Você é um extrator de dados para apólices brasileiras de Seguro D&O
(Directors and Officers / Responsabilidade Civil de Administradores).

Extraia somente dados explicitamente escritos no documento enviado.

Regras:
1. Ignore sumário, glossário e assinaturas.
2. Priorize quadro-resumo, frontispício, condições gerais e cláusulas específicas.
3. Se uma informação não estiver explícita, retorne string vazia, false ou omita o valor numérico.
4. Não invente informação nem use conhecimento externo.
5. Preencha lmi_valor, limite_agregado_valor e premio_valor somente se o valor
   estiver claramente expresso em reais.
6. base_reclamacoes deve reproduzir resumidamente a modalidade de contratação
   explicitamente indicada no documento, por exemplo "À Base de Reclamações"
   ou "À Base de Reclamações com Notificação". Se não estiver explicitamente
   indicada, retorne string vazia
7. cobertura_a, cobertura_b e cobertura_c devem conter o nome da respectiva
   cobertura quando ela estiver expressamente prevista no documento.
   Se a cobertura não estiver identificada, retorne string vazia.
   Não invente nomes de coberturas.
8. custos_defesa_em_adicao deve conter a redação encontrada no documento
   sobre os custos de defesa, indicando se eles estão incluídos no limite,
   em adição ao limite, sujeitos a sublimite ou outra condição expressamente
   prevista. Se essa informação não estiver explícita, retorne string vazia.
   Não interprete nem deduza a condição.
9. Para exclusoes, extraia os títulos ou nomes das exclusões expressamente
   identificadas no documento. Retorne uma lista de strings. Não invente
   exclusões e não transforme exemplos ou referências genéricas em exclusões.
   Para cada exclusão extraída, crie uma evidência separada com campo
   "exclusoes", informando a página em que aquela exclusão aparece e um
   trecho literal curto que contenha o título ou identificação da exclusão.
   Não use apenas o título da seção "Exclusões Gerais" como evidência de
   todas as exclusões.  
10. Para cada dado encontrado, inclua evidência com: campo, página e trecho literal curto.
11. Se não souber a página, use 0.
12. Se o documento for de outro ramo, como Seguro Garantia, identifique isso em
    tipo_documento e não force os campos D&O.
13. Responda exclusivamente no JSON definido pelo schema.
"""


class Evidencia(BaseModel):
    campo: str
    pagina: int = 0
    trecho: str


class ApoliceDO(BaseModel):
    arquivo: str = ""
    seguradora: str = ""
    tomador: str = ""
    processo_susep: str = ""
    tipo_documento: str = ""
    vigencia_inicio: str = ""
    vigencia_fim: str = ""
    base_reclamacoes: str = ""
    lmi_texto: str = ""
    lmi_valor: float | None = None
    limite_agregado_texto: str = ""
    limite_agregado_valor: float | None = None
    premio_texto: str = ""
    premio_valor: float | None = None
    pos_franquia: str = ""
    cobertura_a: str = ""
    cobertura_b: str = ""
    cobertura_c: str = ""
    custos_defesa_em_adicao: str = ""
    prazo_complementar: str = ""
    prazo_suplementar: str = ""
    retroatividade: str = ""
    territorialidade: str = ""
    exclusoes: list[str] = Field(default_factory=list)
    evidencias: list[Evidencia] = Field(default_factory=list)
    confiabilidade: str = "baixa"
    alertas: list[str] = Field(default_factory=list)


def receber(caminho: Path) -> tuple[bytes, str]:
    if not caminho.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}. Confira nome e pasta."
        )

    extensao = caminho.suffix.lower()

    if extensao not in MIME:
        raise ValueError(
            f"Extensão não aceita: {extensao}. Use PDF, PNG, JPG, JPEG ou WEBP."
        )

    dados = caminho.read_bytes()

    if not dados:
        raise ValueError(f"O arquivo '{caminho.name}' está vazio.")

    if len(dados) > MAX_BYTES:
        raise ValueError(
            f"O arquivo '{caminho.name}' excede 20 MB neste MVP."
        )

    return dados, MIME[extensao]


def validar(apolice: ApoliceDO) -> ApoliceDO:
    provas = {e.campo for e in apolice.evidencias if e.trecho.strip()}

    campos_relevantes = [
        "seguradora",
        "processo_susep",
        "tipo_documento",
        "base_reclamacoes",
        "lmi_texto",
        "cobertura_a",
        "cobertura_b",
        "cobertura_c",
        "prazo_complementar",
        "prazo_suplementar",
        "territorialidade",
        "exclusoes",
    ]

    presentes = sum(
        1
        for campo in campos_relevantes
        if getattr(apolice, campo) not in ("", False, [], None)
    )

    comprovados = sum(
        1 for campo in campos_relevantes if campo in provas
    )

    if not apolice.seguradora and apolice.lmi_valor is None:
        apolice.confiabilidade = "baixa"
        apolice.alertas.append(
            "Quase nada foi extraído. Documento ilegível, incompleto ou incompatível com D&O."
        )
    elif comprovados >= 3:
        apolice.confiabilidade = "alta"
    else:
        apolice.confiabilidade = "media"
        apolice.alertas.append(
            "Há campos sem trecho de evidência. Revisão humana recomendada."
        )

    if presentes == 0:
        apolice.alertas.append("Nenhum campo relevante foi preenchido.")

    tipo = apolice.tipo_documento.lower()

    if "garantia" in tipo:
        apolice.confiabilidade = "baixa"
        apolice.alertas.append(
            "Documento identificado como Seguro Garantia, não como D&O. "
            "Use-o apenas como teste técnico; não use esta análise para comparar D&O."
        )

    return apolice


def extrair(caminho: Path, dados: bytes, mime: str) -> ApoliceDO:
    from google import genai
    from google.genai import errors, types

    chave = os.environ.get("GOOGLE_API") or os.environ.get("GOOGLE_API_KEY")

    if not chave:
        raise RuntimeError(
            "GEMINI_API_KEY não encontrada. Confira o arquivo .env."
        )

    #modelo = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    #modelo = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
    modelo = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

    cliente = genai.Client(api_key=chave)

    documento = types.Part.from_bytes(
        data=dados,
        mime_type=mime,
    )

    configuracao = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=SCHEMA,
        temperature=0.1,
    )

    resposta = None

    for tentativa in range(1, 4):
        try:
            resposta = cliente.models.generate_content(
                model=modelo,
                contents=[PROMPT, documento],
                config=configuracao,
            )
            break

        except errors.ServerError as erro:
            if tentativa == 3:
                raise RuntimeError(
                    "O Gemini permaneceu indisponível após 3 tentativas. "
                    "Aguarde alguns minutos e tente novamente."
                ) from erro

            espera = tentativa * 10
            print(
                f"Gemini ocupado ao processar '{caminho.name}' "
                f"(tentativa {tentativa}/3). Nova tentativa em {espera}s..."
            )
            time.sleep(espera)

        except errors.ClientError as erro:
            mensagem = str(erro)

            if "429" in mensagem or "RESOURCE_EXHAUSTED" in mensagem:
                raise RuntimeError(
                    "Cota da API Gemini esgotada. Aguarde a reposição da cota "
                    "ou use um projeto com billing habilitado. "
                    "Nenhum dado foi processado nesta tentativa."
                ) from erro

            raise

    if resposta is None or not resposta.text:
        raise RuntimeError(
            "O Gemini não devolveu texto. Tente novamente mais tarde."
        )

    try:
        apolice = ApoliceDO.model_validate_json(resposta.text)
    except Exception as erro:
        raise RuntimeError(
            "O Gemini respondeu em formato incompatível com o JSON esperado. "
            f"Detalhe: {erro}"
        ) from erro

    apolice.arquivo = caminho.name
    return validar(apolice)


def iniciar_banco(banco: Path) -> None:
    banco.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(banco) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS apolices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arquivo TEXT NOT NULL,
                processado_em TEXT NOT NULL,
                seguradora TEXT,
                tipo_documento TEXT,
                confiabilidade TEXT,
                lmi_valor REAL,
                json_completo TEXT NOT NULL
            )
            """
        )


def salvar(apolice: ApoliceDO, banco: Path) -> int:
    iniciar_banco(banco)

    with sqlite3.connect(banco) as con:
        cursor = con.execute(
            """
            INSERT INTO apolices (
                arquivo,
                processado_em,
                seguradora,
                tipo_documento,
                confiabilidade,
                lmi_valor,
                json_completo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                apolice.arquivo,
                datetime.now(timezone.utc).isoformat(),
                apolice.seguradora,
                apolice.tipo_documento,
                apolice.confiabilidade,
                apolice.lmi_valor,
                apolice.model_dump_json(),
            ),
        )
        return int(cursor.lastrowid)


def listar_apolices(banco: Path) -> list[tuple]:
    iniciar_banco(banco)

    with sqlite3.connect(banco) as con:
        return con.execute(
            """
            SELECT id, arquivo, seguradora, tipo_documento,
                   confiabilidade, lmi_valor, processado_em
            FROM apolices
            ORDER BY id
            """
        ).fetchall()

def verificar_arquivo_existente(banco: Path, nome_arquivo: str) -> list[tuple]:
    iniciar_banco(banco)

    with sqlite3.connect(banco) as con:
        return con.execute(
            """
            SELECT id, seguradora, tipo_documento, processado_em
            FROM apolices
            WHERE arquivo = ?
            ORDER BY id DESC
            """,
            (nome_arquivo,),
        ).fetchall()

def buscar_apolice(banco: Path, apolice_id: int) -> ApoliceDO:
    iniciar_banco(banco)

    with sqlite3.connect(banco) as con:
        linha = con.execute(
            "SELECT json_completo FROM apolices WHERE id = ?",
            (apolice_id,),
        ).fetchone()

    if linha is None:
        raise ValueError(
            f"Não existe apólice salva com ID {apolice_id}. "
            "Use --listar para consultar IDs existentes."
        )

    return ApoliceDO.model_validate_json(linha[0])


def _num(campo: str, valor_a: float | None, valor_b: float | None) -> dict:
    if valor_a is None or valor_b is None:
        return {
            "campo": campo,
            "a": valor_a,
            "b": valor_b,
            "diferenca": "Incomparável: valor ausente em uma ou ambas as apólices.",
            "sinal": "amarelo",
        }

    if valor_a == valor_b:
        return {
            "campo": campo,
            "a": valor_a,
            "b": valor_b,
            "diferenca": "Valores iguais.",
            "sinal": "amarelo",
        }

    maior = "A" if valor_a > valor_b else "B"
    menor_valor = min(valor_a, valor_b)

    percentual = (
        abs(valor_a - valor_b) / menor_valor * 100
        if menor_valor != 0
        else 0
    )

    return {
        "campo": campo,
        "a": valor_a,
        "b": valor_b,
        "diferenca": f"{maior} é {percentual:.0f}% maior.",
        "sinal": "verde" if maior == "A" else "vermelho",
    }


def _bool(campo: str, valor_a: bool, valor_b: bool) -> dict:
    if valor_a == valor_b:
        texto = "Ambos possuem." if valor_a else "Ambos não possuem."
        sinal = "amarelo"
    elif valor_a:
        texto = "Somente A possui."
        sinal = "verde"
    else:
        texto = "Somente B possui."
        sinal = "vermelho"

    return {
        "campo": campo,
        "a": valor_a,
        "b": valor_b,
        "diferenca": texto,
        "sinal": sinal,
    }
def _texto(campo: str, valor_a: str, valor_b: str) -> dict:
    if not valor_a and not valor_b:
        diferenca = "Informação ausente em ambas as apólices."
    elif not valor_a or not valor_b:
        diferenca = "Incomparável: informação ausente em uma das apólices."
    elif valor_a == valor_b:
        diferenca = "Textos iguais."
    else:
        diferenca = "Textos diferentes: requer leitura da cláusula."

    return {
        "campo": campo,
        "a": valor_a,
        "b": valor_b,
        "diferenca": diferenca,
        "sinal": "amarelo",
    }



def comparar(a: ApoliceDO, b: ApoliceDO) -> list[dict]:
    linhas = [
        _num("LMI", a.lmi_valor, b.lmi_valor),
        _num(
            "Limite agregado",
            a.limite_agregado_valor,
            b.limite_agregado_valor,
        ),
        _texto("Cobertura A", a.cobertura_a, b.cobertura_a),
        _texto("Cobertura B", a.cobertura_b, b.cobertura_b),
        _texto("Cobertura C", a.cobertura_c, b.cobertura_c),
        _texto(
            "Custos de defesa em adição ao limite",
            a.custos_defesa_em_adicao,
            b.custos_defesa_em_adicao,
        ),
        _texto(
            "Base de reclamações",
            a.base_reclamacoes,
            b.base_reclamacoes,
        ),
    ]

    campos_texto = [
        ("POS / franquia", "pos_franquia"),
        ("Prazo complementar", "prazo_complementar"),
        ("Prazo suplementar", "prazo_suplementar"),
        ("Retroatividade", "retroatividade"),
        ("Territorialidade", "territorialidade"),
    ]

    for nome, atributo in campos_texto:
        valor_a = getattr(a, atributo)
        valor_b = getattr(b, atributo)

        linhas.append(
            _texto(
                nome,
                valor_a,
                valor_b,
            )
        )

    exclusoes_a = sorted(set(a.exclusoes) - set(b.exclusoes))
    exclusoes_b = sorted(set(b.exclusoes) - set(a.exclusoes))

    linhas.append(
        {
            "campo": "Exclusões exclusivas",
            "a": exclusoes_a,
            "b": exclusoes_b,
            "diferenca": (
                f"Somente em A: {exclusoes_a or 'nenhuma'}; "
                f"somente em B: {exclusoes_b or 'nenhuma'}."
            ),
            "sinal": "amarelo",
        }
    )

    return linhas


def imprimir_comparacao(linhas: list[dict]) -> None:
    print(f"{'CAMPO':<42} {'SINAL':<10} DIFERENÇA")
    print("-" * 110)

    for linha in linhas:
        print(
            f"{linha['campo']:<42} "
            f"{linha['sinal']:<10} "
            f"{linha['diferenca']}"
        )


def imprimir_lista(registros: list[tuple]) -> None:
    if not registros:
        print("Nenhuma apólice salva no banco.")
        return

    print(
        f"{'ID':<5} {'ARQUIVO':<28} {'SEGURADORA':<25} "
        f"{'TIPO':<28} {'CONFIANÇA':<12} {'LMI':<14}"
    )
    print("-" * 125)

    for apolice_id, arquivo, seguradora, tipo, confiabilidade, lmi, _em in registros:
        print(
            f"{apolice_id:<5} "
            f"{arquivo[:27]:<28} "
            f"{(seguradora or '')[:24]:<25} "
            f"{(tipo or '')[:27]:<28} "
            f"{(confiabilidade or ''):<12} "
            f"{str(lmi or ''):<14}"
        )


def demo() -> tuple[ApoliceDO, ApoliceDO]:
    a = ApoliceDO(
        arquivo="demo_a.pdf",
        seguradora="Seguradora A",
        tipo_documento="Apólice D&O",
        lmi_texto="R$ 10.000.000",
        lmi_valor=10_000_000,
        limite_agregado_texto="R$ 10.000.000",
        limite_agregado_valor=10_000_000,
        cobertura_a=True,
        cobertura_b=True,
        cobertura_c=False,
        custos_defesa_em_adicao=True,
        prazo_complementar="36 meses",
        base_reclamacoes=True,
        exclusoes=["dolo", "reclamações conhecidas"],
        evidencias=[
            Evidencia(
                campo="lmi_texto",
                pagina=2,
                trecho="Limite máximo de indenização: R$ 10.000.000",
            ),
            Evidencia(
                campo="seguradora",
                pagina=1,
                trecho="Seguradora A",
            ),
            Evidencia(
                campo="exclusoes",
                pagina=8,
                trecho="Exclusões: dolo e reclamações conhecidas.",
            ),
        ],
    )

    b = ApoliceDO(
        arquivo="demo_b.pdf",
        seguradora="Seguradora B",
        tipo_documento="Apólice D&O",
        lmi_texto="R$ 15.000.000",
        lmi_valor=15_000_000,
        limite_agregado_texto="R$ 15.000.000",
        limite_agregado_valor=15_000_000,
        cobertura_a=True,
        cobertura_b=True,
        cobertura_c=True,
        custos_defesa_em_adicao=False,
        prazo_complementar="12 meses",
        base_reclamacoes=True,
        exclusoes=["dolo", "multas e penalidades"],
        evidencias=[
            Evidencia(
                campo="lmi_texto",
                pagina=1,
                trecho="LMI de R$ 15.000.000",
            ),
            Evidencia(
                campo="seguradora",
                pagina=1,
                trecho="Seguradora B",
            ),
            Evidencia(
                campo="exclusoes",
                pagina=7,
                trecho="Exclusões: dolo e multas e penalidades.",
            ),
        ],
    )

    return validar(a), validar(b)


def processar_arquivos(arquivos: list[str], banco: Path) -> None:
    for nome in arquivos:
        caminho = Path(nome)
        dados, mime = receber(caminho)
        apolice = extrair(caminho, dados, mime)
        apolice_id = salvar(apolice, banco)

        print("\n" + "=" * 110)
        print(f"APÓLICE PROCESSADA E SALVA COM ID {apolice_id}")
        print("=" * 110)
        print(apolice.model_dump_json(indent=2))
        print(
            f"\nConfiabilidade: {apolice.confiabilidade}\n"
            f"Alertas: {apolice.alertas or ['Nenhum']}\n"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pipeline MVP de análise e comparação de apólices D&O."
    )

    parser.add_argument(
        "arquivos",
        nargs="*",
        help="Um ou dois PDFs/imagens para processar.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Executa comparação com dados fictícios, sem chamar Gemini.",
    )
    parser.add_argument(
        "--listar",
        action="store_true",
        help="Lista apólices já salvas no SQLite.",
    )
    parser.add_argument(
        "--comparar",
        nargs=2,
        metavar=("ID_A", "ID_B"),
        type=int,
        help="Compara duas apólices salvas, sem chamar Gemini.",
    )
    parser.add_argument(
        "--banco",
        default=BANCO_PADRAO,
        help=f"Arquivo SQLite. Padrão: {BANCO_PADRAO}",
    )

    args = parser.parse_args()
    banco = Path(args.banco)

    if args.demo:
        a, b = demo()

        print("APÓLICE FICTÍCIA A")
        print(a.model_dump_json(indent=2))

        print("\nCOMPARAÇÃO FICTÍCIA")
        imprimir_comparacao(comparar(a, b))
        return 0

    if args.listar:
        imprimir_lista(listar_apolices(banco))
        return 0

    if args.comparar:
        id_a, id_b = args.comparar
        a = buscar_apolice(banco, id_a)
        b = buscar_apolice(banco, id_b)

        print(f"\nA = ID {id_a}: {a.arquivo} | {a.seguradora}")
        print(f"B = ID {id_b}: {b.arquivo} | {b.seguradora}\n")
        imprimir_comparacao(comparar(a, b))
        return 0

    if not args.arquivos:
        parser.error(
            "Informe arquivo(s), use --demo, --listar ou --comparar ID_A ID_B."
        )

    if len(args.arquivos) > 2:
        parser.error("Informe no máximo dois arquivos por vez.")

    processar_arquivos(args.arquivos, banco)

    print("\nPROCESSAMENTO FINALIZADO.")
    print("Use 'python pipeline.py --listar' para consultar IDs salvos.")
    print(
        "Use 'python pipeline.py --comparar ID_A ID_B' "
        "para comparar sem nova chamada ao Gemini."
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nProcessamento cancelado pelo usuário.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as erro:
        print(f"\nERRO: {erro}", file=sys.stderr)
        raise SystemExit(1)