from typing import Literal, Optional
from pydantic import BaseModel, Field, computed_field, model_validator

# um requisito parcial vale metade de um cumprido no score
PESO_PARCIAL = 0.5


class Requisito(BaseModel):
    requisito: str = Field(description = "O requisito, tal como aparece no anuncio")
    estado : Literal["cumpre", "parcial", "falta", "nao_confirmado"]
    evidencia: Optional[str] = Field (
        default=None,
        description="Repositorio e o que la esta escrito que prova o requisito. Obrigatorio quando o estado é 'cumpre' ou parcial",
                )

    @model_validator(mode="after")
    def evidencia_obrigatoria(self):
        if self.estado in ("cumpre", "parcial") and not self.evidencia:
            raise ValueError(
                f"O requisito '{self.requisito}' esta como '{self.estado}', mas nao tem evidencia."
            )
        return self


class Relatorio(BaseModel):
    vaga : str
    empresa : str
    localizacao : Optional[str] = None
    requisitos : list[Requisito]
    resumo_empresa : str
    sugestoes: list[str]

    @computed_field
    @property
    def score(self) -> int:
        """Percentagem dos requisitos técnicos que o utilizador cumpre, de 0 a 100.

        Calcula-se em código a partir dos estados, para ser sempre igual para os mesmos estados.
        Os 'nao_confirmado' não contam. Se não houver nenhum requisito técnico, não há nada
        a medir e devolve 0.
        """
        cumpre = sum(1 for item in self.requisitos if item.estado == "cumpre")
        parcial = sum(1 for item in self.requisitos if item.estado == "parcial")
        falta = sum(1 for item in self.requisitos if item.estado == "falta")

        total = cumpre + parcial + falta
        if total == 0:
            return 0
        return round(100 * (cumpre + PESO_PARCIAL * parcial) / total)

    @model_validator(mode="after")
    def requisitos_sem_repeticao(self):
        vistos=set()
        for item in self.requisitos:
            chave = item.requisito.strip().lower()
            if chave in vistos:
                raise ValueError(f"o requisito '{item.requisito}' aparece repetido.")
            vistos.add(chave)
        return self
    
        

