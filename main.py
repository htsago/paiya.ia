import logging
from uuid import uuid4
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.chains import (
    safe_invoke, fun_fact_prompt, quiz_prompt, summary_prompt,
    free_prompt_template, get_llm,
    SummaryInput, FunFactResponse, QuizResponse,
    get_fun_fact_groq, get_quiz_groq, get_summary_groq, get_free_prompt_groq
)
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from src.validators import validate_response
from src.opensearch import create_feedback_index_if_not_exists, get_opensearch_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    create_feedback_index_if_not_exists()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process_query")
async def process_query(request: Request):
    data = await request.json()
    query = data.get("query", "").strip()
    length = data.get("length")
    use_case = data.get("use_case")
    provider = data.get("provider", "openai")
    model = data.get("model", None)
    messages = data.get("messages", [])

    logging.info(f"User query: {query} | Use case: {use_case} | Provider: {provider} | Model: {model}")

    if not query:
        return JSONResponse(content={"error": "Query fehlt oder ist leer."}, status_code=422)

    try:
        llm = get_llm(provider=provider, model=model)

        if isinstance(llm, dict) and llm.get("provider") in ["groq", "google", "mistral"]:
            client = llm["client"]
            model = llm["model"]
            temperature = llm["temperature"]

            if use_case == "FreePrompt":
                chat_context = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                full_prompt = f"{chat_context}\nuser: {query}\nassistant:" if chat_context else query
                result = get_free_prompt_groq(full_prompt, client, model, temperature, provider=llm["provider"])
                valid, msg = validate_response("FreePrompt", {"data": result})
                if not valid:
                    return JSONResponse(content={"error": msg}, status_code=422)
                response = {"type": "free_prompt", "data": result}

            elif use_case == "Summary":
                if not length:
                    return JSONResponse(content={"error": "Längenangabe für Zusammenfassung fehlt."}, status_code=422)
                result = get_summary_groq(query, length, client, model, temperature, provider=llm["provider"])
                if "error" in result:
                    return JSONResponse(content={"error": result["error"]}, status_code=500)
                valid, msg = validate_response("Summary", result)
                if not valid:
                    return JSONResponse(content={"error": msg}, status_code=422)
                response = {"type": "summary", **result}

            elif use_case == "Quiz":
                result = get_quiz_groq(query, client, model, temperature, messages=messages, provider=llm["provider"])
                if "error" in result:
                    return JSONResponse(content={"error": result["error"]}, status_code=500)
                valid, msg = validate_response("Quiz", result)
                if not valid:
                    return JSONResponse(content={"error": msg}, status_code=422)
                response = {"type": "quiz", **result}

            elif use_case == "FunFact":
                result = get_fun_fact_groq(query, client, model, temperature, provider=llm["provider"])
                if "error" in result:
                    return JSONResponse(content={"error": result["error"]}, status_code=500)
                valid, msg = validate_response("FunFact", result)
                if not valid:
                    return JSONResponse(content={"error": msg}, status_code=422)
                response = {"type": "fun_fact", **result}

            else:
                return JSONResponse(
                    content={"type": "not_supported", "message": "Diese Anfrage wird nicht unterstützt."},
                    status_code=200
                )

        else:
            if use_case == "FreePrompt":
                if hasattr(llm, "invoke"):
                    chat_messages = messages + [{"role": "user", "content": query}]
                    result = llm.invoke(chat_messages)
                else:
                    chat_context = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                    full_prompt = f"{chat_context}\nuser: {query}\nassistant:" if chat_context else query
                    chain = free_prompt_template | llm | StrOutputParser()
                    result = safe_invoke(chain, {"question": full_prompt}, context="FreePrompt")
                valid, msg = validate_response("FreePrompt", {"data": result})
                if not valid:
                    return JSONResponse(content={"error": msg}, status_code=422)
                response = {"type": "free_prompt", "data": result}

            elif use_case == "Summary":
                if not length:
                    return JSONResponse(content={"error": "Längenangabe für Zusammenfassung fehlt."}, status_code=422)
                parser = JsonOutputParser(pydantic_object=SummaryInput)
                chain = summary_prompt | llm | parser
                result = safe_invoke(chain, {"text": query, "length": length}, context="Summary")
                valid, msg = validate_response("Summary", result)
                if not valid:
                    return JSONResponse(content={"error": msg}, status_code=422)
                response = {"type": "summary", **result}

            elif use_case == "Quiz":
                parser = JsonOutputParser(pydantic_object=QuizResponse)
                chain = quiz_prompt | llm | parser
                prompt_context = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                prompt_with_context = f"{prompt_context}\nuser: {query}" if prompt_context else query
                result = safe_invoke(chain, {"topic": prompt_with_context}, context="Quiz")
                valid, msg = validate_response("Quiz", result)
                if not valid:
                    return JSONResponse(content={"error": msg}, status_code=422)
                response = {"type": "quiz", **result}

            elif use_case == "FunFact":
                parser = JsonOutputParser(pydantic_object=FunFactResponse)
                chain = fun_fact_prompt | llm | parser
                prompt_context = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                prompt_with_context = f"{prompt_context}\nuser: {query}" if prompt_context else query
                result = safe_invoke(chain, {"word": prompt_with_context}, context="FunFact")
                valid, msg = validate_response("FunFact", result)
                if not valid:
                    return JSONResponse(content={"error": msg}, status_code=422)
                response = {"type": "fun_fact", **result}

            else:
                return JSONResponse(
                    content={"type": "not_supported", "message": "Diese Anfrage wird nicht unterstützt."},
                    status_code=200
                )

        return JSONResponse(content=response, status_code=200)

    except ValueError as ve:
        logging.error(f"Validierungsfehler: {ve}")
        return JSONResponse(content={"error": str(ve)}, status_code=422)
    except Exception as e:
        logging.exception(f"Fehler beim Verarbeiten der Anfrage: {e}")
        return JSONResponse(
            content={"error": "Ein unerwarteter Fehler ist aufgetreten."},
            status_code=500
        )

@app.post("/store_feedback")
async def store_feedback(request: Request):
    try:
        data = await request.json()

        thumbs = data.get("thumbs")
        message_index = data.get("message_index")
        model = data.get("model")
        provider = data.get("provider")
        feedback_text = data.get("feedback", "")
        messages = data.get("messages", [])

        # Validierung
        if thumbs not in ["up", "down"]:
            logger.error(f"Ungültiger thumbs-Wert: {thumbs}")
            return JSONResponse(content={"error": "Ungültiger thumbs-Wert"}, status_code=400)

        if not isinstance(message_index, int):
            logger.error(f"Ungültiger message_index-Wert: {message_index}")
            return JSONResponse(content={"error": "message_index muss eine Ganzzahl sein"}, status_code=400)

        if provider not in ["openai", "groq", "google", "mistral"]:
            logger.error(f"Ungültiger provider-Wert: {provider}")
            return JSONResponse(content={"error": "Ungültiger provider-Wert"}, status_code=400)

        # Erstelle das Dokument
        doc = {
            "timestamp": datetime.utcnow().isoformat(),
            "thumbs": thumbs,
            "model": model,
            "provider": provider,
            "message_index": message_index,
            "feedback_text": feedback_text,
            "chat_snapshot": messages,
            "id": str(uuid4())
        }
        logger.info(f"Prepared document: {doc}")

        client = get_opensearch_client()
        response = client.index(index="chat-feedback", body=doc)
        logger.info(f"Document indexed successfully: {response}")

        return JSONResponse(content={"message": "Feedback stored successfully", "doc": doc}, status_code=200)

    except ValueError as ve:
        logger.error(f"Ungültige JSON-Daten: {ve}")
        return JSONResponse(content={"error": "Ungültige JSON-Daten"}, status_code=400)
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Feedbacks: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
