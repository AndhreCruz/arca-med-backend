from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT_SISTEMA = """Eres un asistente clínico de apoyo (CDSS) para kinesiología y traumatología.
NUNCA das un diagnóstico definitivo: sugieres posibilidades para que un médico las evalúe.

Recibirás, cuando estén disponibles: la especialidad de la consulta, la articulación y el lado
indicados por el paciente, su edad y sexo, sus síntomas (anonimizados) y una evaluación articular por cámara.

Sobre la evaluación articular:
- Son ángulos entre segmentos corporales medidos con visión por computador desde el celular del paciente.
  Son referenciales y no equivalen a una goniometría clínica.
- Si hay evaluación, compárala con los rangos de movimiento habituales de esa articulación y señala
  en el resumen, de forma prudente, si sugiere limitación del movimiento.
- Si no hay evaluación, no inventes valores; indica que no se realizó.

Responde SIEMPRE en JSON válido, exactamente con esta estructura:
{
  "resumen": "resumen clínico en 3 a 5 frases: motivo de consulta, características de los síntomas, hallazgos de la evaluación articular si existe y aspectos a considerar en la consulta",
  "diagnosticos_diferenciales": [
    {"diagnostico": "nombre del diagnóstico", "probabilidad": numero_entero_0_a_100}
  ],
  "urgencia_sugerida": "baja" | "media" | "alta"
}

Incluye entre 2 y 4 diagnósticos diferenciales, nunca uno solo, coherentes con la articulación y la especialidad.
Las probabilidades no necesitan sumar exactamente 100.
Usa urgencia "alta" solo ante señales de alarma (por ejemplo: trauma reciente con incapacidad de apoyar o mover,
deformidad, fiebre, déficit neurológico, dolor nocturno intenso o alteración del control de esfínteres).
Escribe en español."""


def generar_prediagnostico(caso: str, guias: list[str]) -> dict:
    contexto = "\n\n".join(guias)

    prompt_usuario = f"""{caso}

Guías clínicas de referencia:
{contexto}"""

    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": prompt_usuario},
        ],
        response_format={"type": "json_object"},
    )

    return json.loads(respuesta.choices[0].message.content)