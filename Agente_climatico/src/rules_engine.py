"""Regras de decisão para envio de alertas aos segurados."""

IDADE_ATENCAO_PRIORITARIA = 60

EVENTOS_SAUDE_SENSIVEIS = {
    "Calor Extremo",
    "Frio Intenso",
    "Baixa Umidade",
    "Qualidade do Ar Ruim",
}

REGRAS_NEGOCIO = {
    "Auto": {
        "Chuva Forte": (
            "A chuva forte pode causar alagamentos, reduzir a visibilidade "
            "e deixar a pista escorregadia."
        ),
        "Tempestade": (
            "A tempestade pode reduzir a visibilidade e provocar alagamentos "
            "ou queda de objetos sobre o veículo."
        ),
        "Ventos Fortes": (
            "Os ventos fortes aumentam o risco de queda de galhos e objetos "
            "sobre o veículo."
        ),
    },
    "Residencial": {
        "Chuva Forte": (
            "A chuva forte aumenta o risco de infiltração e alagamento no imóvel."
        ),
        "Tempestade": (
            "A tempestade pode causar infiltrações, danos elétricos e outros "
            "danos ao imóvel."
        ),
        "Ventos Fortes": (
            "Os ventos fortes aumentam o risco de destelhamento e queda de "
            "árvores ou objetos sobre o imóvel."
        ),
    },
    "Saúde / Vida": {
        "Calor Extremo": (
            "O calor extremo pode aumentar os riscos à saúde associados à "
            "exposição prolongada a altas temperaturas."
        ),
        "Frio Intenso": (
            "O frio intenso pode aumentar os riscos à saúde associados à "
            "exposição prolongada a baixas temperaturas."
        ),
        "Baixa Umidade": (
            "A baixa umidade pode causar ressecamento, desconforto respiratório "
            "e aumentar o risco de desidratação."
        ),
        "Qualidade do Ar Ruim": (
            "A qualidade do ar está classificada como ruim ou muito ruim, "
            "indicando a necessidade de reduzir a exposição prolongada."
        ),
    },
}


def obter_eventos(clima):
    """Obtém e normaliza a lista de eventos identificados pelo serviço climático."""
    eventos = clima.get("eventos_relevantes")

    if not isinstance(eventos, (list, tuple, set)):
        evento_antigo = clima.get("evento_relevante")
        eventos = [evento_antigo] if evento_antigo else []

    eventos = list(eventos)

    qualidade_ar = clima.get("qualidade_ar") or {}

    evento_qualidade_ar = qualidade_ar.get("evento_relevante")
    if evento_qualidade_ar:
        eventos.append(evento_qualidade_ar)


    # Remove valores vazios e duplicados, preservando a ordem recebida.
    return list(dict.fromkeys(evento for evento in eventos if evento))


def verificar_necessidade_alerta(cliente, clima):
    """Decide se os eventos detectados representam risco para o seguro contratado."""
    eventos = obter_eventos(clima)

    if not eventos:
        return False, "Sem eventos climáticos críticos."

    tipo_seguro = str(cliente.get("seguro", "")).strip()
    regras_do_seguro = REGRAS_NEGOCIO.get(tipo_seguro, {})

    motivos = [
        regras_do_seguro[evento]
        for evento in eventos
        if evento in regras_do_seguro
    ]

    if not motivos:
        return False, "Os eventos detectados não afetam a apólice simulada."

    idade = cliente.get("idade")

    if (
            tipo_seguro == "Saúde / Vida"
            and idade is not None
            and idade >= IDADE_ATENCAO_PRIORITARIA
            and any(evento in EVENTOS_SAUDE_SENSIVEIS for evento in eventos)
    ):
        motivos.append(
            "A faixa etária do segurado indica necessidade de "
            "atenção preventiva adicional."
        )

    return True, " ".join(motivos)
