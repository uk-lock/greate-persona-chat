"""チャット関連のルーター。"""

import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse

from app.api.dependencies import (
    get_chat_service,
    get_current_user,
    get_user_id_for_rate_limit,
)
from app.api.rate_limit import limiter
from app.api.schemas.chat import (
    ChatMessageResponse,
    ChatResponse,
    ChatStreamEvent,
    CreateChatRequest,
    ErrorEvent,
    MessageEvent,
    PersonaParticipant,
    PostMessageRequest,
    ThinkingEvent,
    TitleEvent,
    UserParticipant,
)
from app.api.schemas.chat import Participant as ParticipantSchema
from app.config import constants
from app.models.chat import Chat, ChatMode
from app.models.user import User
from app.services.chat_service import (
    ChatService,
    MessageTurnEvent,
    ThinkingTurnEvent,
    TitleTurnEvent,
)
from app.services.exceptions import ExternalServiceError

router = APIRouter(prefix="/chats", tags=["chats"])


def _build_chat_response(chat: Chat) -> ChatResponse:
    """chat_personas（sort_no順にロード済み）からparticipantsを組み立てる。"""
    participants: list[ParticipantSchema] = []
    if chat.chat_mode == ChatMode.USER_PARTICIPATED:
        participants.append(UserParticipant(type="USER", name="あなた"))
    participants.extend(
        PersonaParticipant(
            type="PERSONA",
            persona_id=chat_persona.persona_id,
            name=chat_persona.persona.name,
            image_url=chat_persona.persona.image_url,
        )
        for chat_persona in chat.chat_personas
    )
    return ChatResponse(
        chat_id=chat.public_id,
        title=chat.title,
        chat_mode=chat.chat_mode,
        updated_at=chat.updated_at,
        participants=participants,
    )


def _format_sse_event(event: ChatStreamEvent) -> bytes:
    """SSEイベントの1件（dataフレーム）にシリアライズする。"""
    return f"data: {event.model_dump_json()}\n\n".encode()


async def _stream_turns(
    chat_id: int,
    current_user: User,
    chat_mode: ChatMode,
    request: Request,
    chat_service: ChatService,
) -> AsyncIterator[bytes]:
    """ChatService.stream_turnsが発行するイベントをSSEフレームへ変換する。

    LLM呼び出しの失敗（tenacity相当のリトライを使い切った場合。
    app/llm/retry.py参照）は、ヘッダー送信後のためHTTPステータスには変換できず、
    `error`イベントとして配信してストリームを終了する。
    """
    try:
        async for event in chat_service.stream_turns(
            chat_id, current_user, chat_mode, request
        ):
            if isinstance(event, ThinkingTurnEvent):
                yield _format_sse_event(ThinkingEvent(persona_id=event.persona.id))
            elif isinstance(event, MessageTurnEvent):
                yield _format_sse_event(
                    MessageEvent(
                        message=ChatMessageResponse.model_validate(event.message)
                    )
                )
            elif isinstance(event, TitleTurnEvent):
                yield _format_sse_event(TitleEvent(title=event.title))
    except ExternalServiceError as exc:
        yield _format_sse_event(ErrorEvent(message=str(exc)))


@router.get("")
async def get_chats(
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> list[ChatResponse]:
    """ログインユーザのチャット一覧をupdated_at降順で取得する。"""
    chats = await chat_service.get_by_user(current_user)
    return [_build_chat_response(chat) for chat in chats]


@router.post("", status_code=201)
async def create_chat(
    body: CreateChatRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """新規チャットを作成する。

    Raises:
        NotFoundError: persona_idsに存在しない、または論理削除済みのペルソナが含まれる場合（404に変換される）。
    """
    chat = await chat_service.create(current_user, body.persona_ids, body.chat_mode)
    return _build_chat_response(chat)


@router.get("/{chat_id}")
async def get_chat(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """チャット単体を取得する（S03ヘッダー表示用：タイトル・chat_mode・参加者）。

    Raises:
        NotFoundError: チャットが存在しない、または論理削除済みの場合（404に変換される）。
        ForbiddenError: 他ユーザーが作成したチャットの場合（403に変換される）。
    """
    internal_chat_id = await chat_service.resolve_internal_id(chat_id)
    chat = await chat_service.get_by_id(internal_chat_id, current_user)
    return _build_chat_response(chat)


@router.delete("/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> Response:
    """チャットを論理削除する。

    Raises:
        NotFoundError: チャットが存在しない、または論理削除済みの場合（404に変換される）。
        ForbiddenError: 他ユーザーが作成したチャットの場合（403に変換される）。
    """
    internal_chat_id = await chat_service.resolve_internal_id(chat_id)
    await chat_service.delete(internal_chat_id, current_user)
    return Response(status_code=204)


@router.get("/{chat_id}/messages")
async def get_messages(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> list[ChatMessageResponse]:
    """チャットのメッセージ一覧をsort_no順で取得する。

    Raises:
        NotFoundError: チャットが存在しない、または論理削除済みの場合（404に変換される）。
        ForbiddenError: 他ユーザーが作成したチャットの場合（403に変換される）。
    """
    internal_chat_id = await chat_service.resolve_internal_id(chat_id)
    messages = await chat_service.get_messages(internal_chat_id, current_user)
    return [ChatMessageResponse.model_validate(message) for message in messages]


@router.post("/{chat_id}/messages")
@limiter.limit(
    f"{constants.RATE_LIMIT_MESSAGE_PER_MINUTE}/minute",
    key_func=get_user_id_for_rate_limit,
    error_message="送信回数が上限に達しました。しばらくしてから再度お試しください。",
)
@limiter.limit(
    f"{constants.RATE_LIMIT_MESSAGE_PER_DAY}/day",
    key_func=get_user_id_for_rate_limit,
    error_message="本日の送信回数の上限に達しました。日付が変わってから再度お試しください。",
)
async def post_message(
    request: Request,
    chat_id: uuid.UUID,
    body: PostMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    """会話を進行させ、生成されたイベント（考え中・発言・タイトル更新）をSSE
    （text/event-stream）で配信する。

    USER_PARTICIPATEDのユーザー発言保存・チャット存在確認/権限確認はLLM呼び出しを
    伴わないため、StreamingResponse開始前に実行し、例外を通常のHTTPエラー
    レスポンス（404/403/400）として返せるようにする。LLM呼び出し自体（話者選択・
    応答生成・タイトル生成）はストリーム開始後にのみ発生するため、失敗時は
    `error`イベントとして配信する（`_stream_turns`参照）。

    Raises:
        NotFoundError: チャットが存在しない、または論理削除済みの場合（404に変換される）。
        ForbiddenError: 他ユーザーが作成したチャットの場合（403に変換される）。
        ValidationError: USER_PARTICIPATEDモードでmessageが空の場合（400に変換される）。
    """
    internal_chat_id = await chat_service.resolve_internal_id(chat_id)
    chat_mode = await chat_service.get_chat_mode(internal_chat_id, current_user)
    if chat_mode == ChatMode.USER_PARTICIPATED:
        await chat_service.save_user_message(
            internal_chat_id, current_user, body.message
        )
    return StreamingResponse(
        _stream_turns(internal_chat_id, current_user, chat_mode, request, chat_service),
        media_type="text/event-stream",
    )


@router.post("/{chat_id}/stop", status_code=204)
async def stop_chat(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> Response:
    """自動進行中・連鎖発言中の会話を中断する。

    Raises:
        NotFoundError: チャットが存在しない、または論理削除済みの場合（404に変換される）。
        ForbiddenError: 他ユーザーが作成したチャットの場合（403に変換される）。
    """
    internal_chat_id = await chat_service.resolve_internal_id(chat_id)
    await chat_service.stop(internal_chat_id, current_user)
    return Response(status_code=204)
