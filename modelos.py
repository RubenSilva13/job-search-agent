from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

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
    score: int = Field(ge=0, le=100, description="compatibilidade de 0 a 100")
    requisitos : list[Requisito]
    resumo_empresa : str
    sugestoes: list[str]

    @model_validator(mode="after")
    def requisitos_sem_repeticao(self):
        vistos=set()
        for item in self.requisitos:
            chave = item.requisito.strip().lower()
            if chave in vistos:
                raise ValueError(f"o requisito '{item.requisito}' aparece repetido.")
            vistos.add(chave)
        return self
    
        

