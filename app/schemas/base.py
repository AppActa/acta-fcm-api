from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class ModeloACTA(BaseModel):
    # Gera aliases camelCase dos atributos e também aceita os nomes padrão dos atributos
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)