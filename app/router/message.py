from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from itertools import chain
import json
import logging

from ..crud.message import get_user_messages as crud_get_user_messages
from ..database import get_db
from ..enums.message_role import MessageRole
from ..models.message import Message
from ..models.user import User
from ..schemas import AIRequest, AIResponse, MessageResponse
from ..services.groq_service import groq_service



router = APIRouter(prefix="/messages", tags=["messages"])
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
                    You are the Gift App that can search the web! 

                    You generate gift ideas that feel thoughtful, specific, and genuinely useful.
                    Your output must be in structured Markdown.
                    Do not write introductions or conclusions.
                    Start directly with the gift suggestions.

                    Each gift must:
                    - Have a clear heading with the actual product's name
                    - Include a short explanation of why it works
                    - Include the current price or a price range
                    - Include one or more links to websites or social media business pages
                    where the gift can be bought

                    Prefer products that are widely available and well-reviewed.
                    If you can't find a working link, say so rather than guessing.

                    If the user mentions a location, situation, or constraint,
                    adapt the gift ideas and add another short section 
                    under each gift that guides the user to get the gift in that 
                    constrained context.

                    After the gift ideas, include a section titled "Questions for you"
                    with clarifying questions that would help improve the recommendations.

                    Finish with a section with H2 heading titled "Wanna browse yourself?"
                    with links to various ecommerce sites with relevant search queries and filters 
                    already applied.
                """


GIFT_SCHEMA =   {
    "type": "json_schema",
    "json_schema": {
        "name": "gift_suggestions",
        "schema": {
            "type": "object",
            "properties": {
                "gifts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price_range": {"type": "string"},
                            "why_its_good": {"type": "string"},
                        },
                        "required": [
                            "name",
                            "price_range",
                            "why_its_good"
                        ],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["gifts"],
            "additionalProperties": False
        },
        "strict": True
    }
}


def _add_few_shot_examples(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    few_shot_examples = [
        {
            "role": "user",
            "content": "I need a gift for my 10-year-old niece who loves science and space."
        },
        {
            "role": "assistant",
            "content":  """
                            ### Travel Art Kit for Niece (Compact & Portable)

                            A small, kid-friendly arts & crafts item that's easy to pack and perfect for a quick creative distraction during travel.

                            **How to get it:**
                            1. Head to Dubai International Airport (DXB) and proceed to Terminal 3 Departures.
                            2. Visit Dubai Duty Free or a nearby WHSmith that carries kids’ stationery.
                            3. Ask for compact arts & crafts kits or a coloring book with pencils.
                            4. Choose a lightweight option suitable for carry-on.
                            5. Request gift wrapping if available.

                            ---

                            ### Mini Football Keychain for Nephew

                            A light, inexpensive football-themed souvenir that’s easy to carry and perfect for an airport purchase.

                            **How to get it:**
                            1. Visit Dubai Duty Free or a souvenir shop near the gates.
                            2. Ask for football-themed keychains or small sports souvenirs.
                            3. Check toy or sports sections if needed.
                            4. Purchase and pack securely.

                            ---

                            ## Questions for you
                            1. What are the ages of your niece and nephew?
                            2. Do you have a budget per gift?
                            3. Are you departing from Terminal 3?
                            4. Does your nephew support a specific team?
                        """
        },
        {
            "role": "user",
            "content": "I'm looking for a birthday gift for my 25-year-old brother. He loves hip-hop music, especially rap and vinyl records. My budget is around $50."
        },
        {
            "role": "assistant",
            "content": """
                            ### Vinyl Record from His Favorite Rap Artist

                            A vinyl record from one of his favorite hip-hop artists would make a thoughtful and personal birthday gift, especially if he enjoys collecting music.

                            **How to get it:**
                            1. Identify his favorite rap artists or albums.
                            2. Look for special editions or classic albums on vinyl.
                            3. Check local record stores or online music retailers.
                            4. Make sure the record is compatible with his turntable.
                            5. Add a handwritten birthday note to make the gift more personal.

                            ---

                            ### Hip-Hop Merchandise

                            A T-shirt, hoodie, or cap featuring his favorite rapper or hip-hop brand is another good option.

                            **How to get it:**
                            1. Find out which artists or brands he likes.
                            2. Browse official artist merchandise stores.
                            3. Choose an item that fits his style.
                            4. Check sizing and delivery availability.

                            ---

                            ## Questions for you
                            1. Who are his favorite rappers?
                            2. Does he own a vinyl record player?
                            3. Would he prefer music-related gifts or clothing?
                        """
        }
    ]

    return few_shot_examples + messages

@router.get("/user/{user_id}", response_model=list[MessageResponse])
def get_user_messages(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return crud_get_user_messages(db, user_id)


@router.post("/user/{user_id}", response_model=AIResponse)
def create_prompt(
    user_id: int,
    entry: AIRequest,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    messages = [
        {"role": message.role.value, "content": message.content}
        for message in crud_get_user_messages(db, user_id)
    ]

    _add_few_shot_examples(messages)

    try:
        response = groq_service.generate_response(
            system_prompt=SYSTEM_PROMPT,
            messages=messages,
            user_prompt=entry.prompt,
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate AI response",
        )

    db.add_all([
        Message(
            user_id=user_id,
            role=MessageRole.user,
            content=entry.prompt,
        ),
        Message(
            user_id=user_id,
            role=MessageRole.assistant,
            content=response,
        )
    ])

    db.commit()

    return AIResponse(response=response)


@router.post("/user/{user_id}/stream")
def create_prompt_stream(
    user_id: int,
    entry: AIRequest,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    messages = [
        {"role": message.role.value, "content": message.content}
        for message in crud_get_user_messages(db, user_id)
    ]

    _add_few_shot_examples(messages)


    db.add(
        Message(
            user_id=user_id,
            role=MessageRole.user,
            content=entry.prompt,
        )
    )

    def generate():
        chunks = []

        try:
            for chunk in groq_service.generate_response_stream(
                system_prompt=SYSTEM_PROMPT,
                messages=messages,
                user_prompt=f"Generate fresh gift ideas for this new user request: {entry.prompt}",
            ):
                chunks.append(chunk)

                yield (
                    f"event: token\n"
                    f"data: {json.dumps({'content': chunk})}\n\n"
                )

            response = "".join(chunks)

            db.add(
                Message(
                    user_id=user_id,
                    role=MessageRole.assistant,
                    content=response,
                )
            )
            db.commit()

            yield "event: done\ndata: {}\n\n"

        except Exception:
            db.rollback()
            logger.exception("Groq streaming response failed")

            yield (
                "event: error\n"
                f"data: {json.dumps({'detail': 'Failed to generate AI response'})}\n\n"
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )