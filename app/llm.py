from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generar_prediagnostico(sintoma_anonimizado: str, guias: list[str]) -> dict:
    contexto = "\n\n".join(guias)

    prompt_sistema = """Eres un asistente clinico de apoyo (CDSS) para kinesiologia y traumatologia.
NUNCA das un diagnostico definitivo. Tu rol es sugerir posibilidades para que un medico las evalue.
Responde SIEMPRE en formato JSON valido, exactamente con esta estructura:
{
  "resumen": "resumen breve del caso en 1-2 frases",
  "diagnosticos_diferenciales": [
    {"diagnostico": "nombre del diagnostico", "probabilidad": numero_entero_0_a_100}
  ],
  "urgencia_sugerida": "baja" | "media" | "alta"
}
Incluye entre 2 y 4 diagnosticos diferenciales, nunca uno solo. Las probabilidades no necesitan sumar exactamente 100."""

    prompt_usuario = f"""Sintoma del paciente: {sintoma_anonimizado}

Guias clinicas de referencia:
{contexto}"""

    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario},
        ],
        response_format={"type": "json_object"},
    )

    return json.loads(respuesta.choices[0].message.content)