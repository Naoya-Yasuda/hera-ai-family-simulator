"""
Google ADKベースのAIファミリー・シミュレーター
FastAPIサーバー
"""

import os
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

from agents.hera.adk_hera_agent import ADKHeraAgent


# 環境変数から設定を取得
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="AIファミリー・シミュレーター",
    description="Google ADKベースの家族愛の神ヘーラーエージェント",
    version="2.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# グローバルエージェントインスタンス
hera_agent = None


class SessionRequest(BaseModel):
    """セッション開始リクエスト"""
    session_id: str


class MessageRequest(BaseModel):
    """メッセージ送信リクエスト"""
    session_id: str
    message: str


class MessageResponse(BaseModel):
    """メッセージ応答"""
    text_response: str
    audio_response: Optional[bytes] = None
    conversation_state: str
    information_progress: Dict[str, bool]
    is_complete: bool


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の初期化"""
    global hera_agent
    try:
        hera_agent = ADKHeraAgent(
            project_id=PROJECT_ID,
            location=LOCATION,
            gemini_api_key=GEMINI_API_KEY
        )
        print("✅ ヘーラーエージェントが初期化されました")
    except Exception as e:
        print(f"❌ エージェントの初期化に失敗: {e}")


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "AIファミリー・シミュレーター",
        "version": "2.0.0",
        "agent": "Google ADK ヘーラーエージェント"
    }


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "agent_initialized": hera_agent is not None}


@app.post("/session/start")
async def start_session(request: SessionRequest):
    """セッション開始"""
    if not hera_agent:
        raise HTTPException(status_code=500, detail="エージェントが初期化されていません")

    try:
        greeting = await hera_agent.start_session(request.session_id)
        return {
            "session_id": request.session_id,
            "greeting": greeting,
            "status": "started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"セッション開始に失敗: {str(e)}")


@app.post("/session/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    """メッセージ送信"""
    if not hera_agent:
        raise HTTPException(status_code=500, detail="エージェントが初期化されていません")

    try:
        response = await hera_agent.process_message(
            user_message=request.message,
            audio_data=None
        )

        return MessageResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"メッセージ処理に失敗: {str(e)}")


@app.post("/session/audio")
async def send_audio_message(
    session_id: str,
    audio_file: UploadFile = File(...)
):
    """音声メッセージ送信"""
    if not hera_agent:
        raise HTTPException(status_code=500, detail="エージェントが初期化されていません")

    try:
        audio_data = await audio_file.read()
        response = await hera_agent.process_message(
            user_message="",  # 音声からテキストに変換される
            audio_data=audio_data
        )

        return MessageResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音声メッセージ処理に失敗: {str(e)}")


@app.get("/session/{session_id}/profile")
async def get_user_profile(session_id: str):
    """ユーザープロファイル取得"""
    if not hera_agent:
        raise HTTPException(status_code=500, detail="エージェントが初期化されていません")

    try:
        profile = hera_agent.get_user_profile()
        return {
            "session_id": session_id,
            "profile": profile.dict(),
            "is_complete": hera_agent.is_information_complete()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"プロファイル取得に失敗: {str(e)}")


@app.post("/session/{session_id}/end")
async def end_session(session_id: str):
    """セッション終了"""
    if not hera_agent:
        raise HTTPException(status_code=500, detail="エージェントが初期化されていません")

    try:
        session_info = await hera_agent.end_session()
        return {
            "session_id": session_id,
            "session_info": session_info,
            "status": "ended"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"セッション終了に失敗: {str(e)}")


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket接続（リアルタイム対話）"""
    await websocket.accept()

    if not hera_agent:
        await websocket.close(code=1011, reason="エージェントが初期化されていません")
        return

    try:
        # セッション開始
        greeting = await hera_agent.start_session(session_id)
        await websocket.send_json({
            "type": "greeting",
            "message": greeting,
            "session_id": session_id
        })

        while True:
            # クライアントからのメッセージを受信
            data = await websocket.receive_json()

            if data.get("type") == "message":
                # テキストメッセージを処理
                response = await hera_agent.process_message(
                    user_message=data["message"],
                    audio_data=None
                )

                await websocket.send_json({
                    "type": "response",
                    "data": response
                })

            elif data.get("type") == "audio":
                # 音声メッセージを処理
                audio_data = data.get("audio_data")
                response = await hera_agent.process_message(
                    user_message="",
                    audio_data=audio_data
                )

                await websocket.send_json({
                    "type": "response",
                    "data": response
                })

            elif data.get("type") == "close":
                # セッション終了
                session_info = await hera_agent.end_session()
                await websocket.send_json({
                    "type": "session_ended",
                    "data": session_info
                })
                break

    except Exception as e:
        await websocket.close(code=1011, reason=f"エラー: {str(e)}")


@app.get("/session/{session_id}/audio/{message_id}")
async def get_audio_response(session_id: str, message_id: str):
    """音声応答を取得"""
    # 実装は必要に応じて追加
    return {"message": "音声応答機能は実装中です"}


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
