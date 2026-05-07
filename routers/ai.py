import json
import os
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from groq import Groq
from sqlalchemy.orm import Session

import schemmas
from auth import get_current_user
from controllers.ai_agent import extract_search_intent, search_companies, search_lodgings, search_restaurants, search_experiences, search_producers, search_products
from database import get_db

router = APIRouter(prefix="/ai", tags=["ai"])

TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "qwen/qwen3-32b")
APP_SYSTEM_INSTRUCTION = os.getenv(
    "AI_SYSTEM_INSTRUCTION",
    (
        "Voce e a Niassa AI, assistente oficial do app Niassa Avanca. "
        "Quando perguntarem quem te criou, quem te desenvolveu ou de quem e o app, explique isso com clareza: "
        "a Bluespark MZ e a empresa de desenvolvimento e O Destaque e o dono da plataforma Niassa Avanca. "
        "A plataforma Niassa Avanca e um ecossistema completo que inclui: "
        "- Mercado digital onde empresas podem postar e vender produtos "
        "- Hotéis e alojamentos com reservas online "
        "- Restaurantes com menus e reservas "
        "- Produtores agrícolas e fornecedores "
        "- Experiências turísticas e atividades "
        "- Empresas e prestadores de serviços diversos "
        "Ajude utilizadores com duvidas sobre posts, natureza, turismo, agricultura, uso do aplicativo e seguranca. "
        "Responda sempre em portugues simples, natural, objetiva e amigavel. "
        "Nao invente parcerias, empresas, autores ou tecnologias se isso nao tiver sido informado."
        "Voce foi criada pela Bluespark MZ em parceria com O Destaque, proprietario da plataforma. "
    ),
)


def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY nao configurada")
    return Groq(api_key=api_key)


def _build_messages(payload: schemmas.AIChatRequest, context: str = "") -> list[dict[str, str]]:
    system_instruction = APP_SYSTEM_INSTRUCTION
    if context:
        system_instruction += f"\n\n## Informações de Empresas Disponíveis\n{context}"
    
    messages: list[dict[str, str]] = [{"role": "system", "content": system_instruction}]
    for item in payload.history[-10:]:
        messages.append({"role": item.role, "content": item.content.strip()})
    messages.append({"role": "user", "content": payload.message.strip()})
    return messages


def _build_context_from_search(intent: str, params: dict, db: Session) -> str:
    """Build context string from database search results."""
    context = ""
    try:
        if intent == "lodgings":
            results = search_lodgings(db, query=params.get("query", ""), location=params.get("location"), limit=3)
            if results:
                context = "Alojamentos disponíveis em Niassa:\n"
                for r in results:
                    context += f"- {r['name']} em {r['location']}: {r['description']}\n"
        elif intent == "restaurants":
            results = search_restaurants(db, query=params.get("query", ""), location=params.get("location"), limit=3)
            if results:
                context = "Restaurantes disponíveis:\n"
                for r in results:
                    context += f"- {r['name']} em {r['location']}: {r['description']}\n"
        elif intent == "experiences":
            results = search_experiences(db, query=params.get("query", ""), location=params.get("location"), limit=3)
            if results:
                context = "Experiências turísticas disponíveis:\n"
                for r in results:
                    context += f"- {r['name']} em {r['location']}: {r['description']}\n"
        elif intent == "producers":
            results = search_producers(db, query=params.get("query", ""), location=params.get("location"), limit=3)
            if results:
                context = "Produtores disponíveis:\n"
                for r in results:
                    context += f"- {r['name']} em {r['location']}: {r['description']}\n"
        elif intent == "products":
            results = search_products(db, query=params.get("query", ""), limit=3)
            if results:
                context = "Produtos disponíveis no mercado:\n"
                for r in results:
                    company_name = r.get('producer_name', 'Produtor desconhecido')
                    context += f"- {r['name']} de {company_name}: {r['description']}\n"
        elif intent == "companies":
            results = search_companies(db, query=params.get("query", ""), location=params.get("location"), limit=3)
            if results:
                context = "Empresas parceiras Niassa:\n"
                for r in results:
                    context += f"- {r['name']} ({r['type']}) em {r['location']}: {r['description']}\n"
        
        if context:
            print(f"[AI Agent] Intent: {intent} | Context built with {len(results) if 'results' in locals() else 0} results")
        else:
            print(f"[AI Agent] Intent: {intent} | No results found")
    except Exception as e:
        print(f"[AI Agent] Erro ao buscar contexto para intent '{intent}': {e}")
        import traceback
        traceback.print_exc()
    
    return context


def _extract_delta_text(chunk) -> str:
    choices = getattr(chunk, "choices", None) or []
    if not choices:
        return ""
    delta = getattr(choices[0], "delta", None)
    if not delta:
        return ""
    content = getattr(delta, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            text = getattr(item, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "".join(parts)
    return ""


def _build_completion(client: Groq, payload: schemmas.AIChatRequest, stream: bool, context: str = ""):
    messages = _build_messages(payload, context)
    return client.chat.completions.create(
        model=TEXT_MODEL,
        messages=messages,
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=0.95,
        reasoning_effort="default",
        stream=stream,
        stop=None,
    )


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat", response_model=schemmas.AIChatResponse)
def chat_with_ai(
    payload: schemmas.AIChatRequest,
    db: Session = Depends(get_db),
):
    client = _get_client()
    
    # Try to detect search intent and enrich context
    context = ""
    intent, params = extract_search_intent(payload.message)
    if intent:
        params["query"] = payload.message
        context = _build_context_from_search(intent, params, db)
    
    try:
        completion = _build_completion(client, payload, stream=False, context=context)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao comunicar com Groq: {exc}") from exc

    reply = (getattr(completion, "choices", [None])[0].message.content if getattr(completion, "choices", None) else "") or ""
    reply = reply.strip()
    if not reply:
        raise HTTPException(status_code=502, detail="Groq nao devolveu texto")
    return schemmas.AIChatResponse(reply=reply, model=TEXT_MODEL)


@router.post("/chat/stream")
def chat_with_ai_stream(
    payload: schemmas.AIChatRequest,
    db: Session = Depends(get_db),
):
    client = _get_client()
    
    # Try to detect search intent and enrich context
    context = ""
    intent, params = extract_search_intent(payload.message)
    print(f"[AI Chat] User message: {payload.message}")
    print(f"[AI Chat] Detected intent: {intent}")
    
    if intent:
        params["query"] = payload.message
        context = _build_context_from_search(intent, params, db)
        print(f"[AI Chat] Context length: {len(context)}")

    def event_stream() -> Iterator[str]:
        full_text = ""
        yield _sse_event("start", {"model": TEXT_MODEL})
        try:
            completion = _build_completion(client, payload, stream=True, context=context)
            for chunk in completion:
                delta_text = _extract_delta_text(chunk)
                if not delta_text:
                    continue
                full_text += delta_text
                yield _sse_event("delta", {"text": delta_text, "full_text": full_text})
            yield _sse_event("done", {"reply": full_text, "model": TEXT_MODEL})
        except Exception as exc:
            yield _sse_event("error", {"detail": f"Falha ao comunicar com Groq: {exc}"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
