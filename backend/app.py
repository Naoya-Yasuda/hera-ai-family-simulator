import os # APIキーを読み込むためにosモジュールを追加
import google.generativeai as genai # Gemini AIライブラリをインポート
from dotenv import load_dotenv # .envファイルを読み込むライブラリをインポート
from flask import Flask, jsonify, request

# --- 1. APIキーとAIモデルの準備 ---

# .envファイルから環境変数を読み込む
load_dotenv() 

# .envに保存したAPIキーを読み込む
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# APIキーを使ってGemini AIを設定
genai.configure(api_key=GOOGLE_API_KEY)

# 使用するAIモデル（Gemini Pro）を指定
model = genai.GenerativeModel('gemini-2.0-flash')

# --- 2. Flaskアプリ（司令塔）の準備 ---
app = Flask(__name__)

# --- 3. 「窓口（API）」の作成 ---

@app.route("/v1/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})

@app.route("/v1/simulate", methods=["POST"])
def simulate_family():
    try:
        # --- 4. フロントエンドからデータを受け取る ---
        data = request.get_json()
        
        age = data.get("age")
        income_range = data.get("income") # "middle" など
        lifestyle = data.get("lifestyle", {})
        area = lifestyle.get("area") # "urban" など
        hobby = lifestyle.get("hobby", "特になし") # 趣味

        print(f"--- AIへの入力データ: 年齢{age}, 収入{income_range}, 地域{area}, 趣味{hobby} ---")

        # --- 5. AIに「指示書（プロンプト）」を送る ---

        # AIに「未来のストーリー」を作ってもらうための指示書
        story_prompt = f"""
        あなたは、ポジティブな未来を描くシナリオライターです。
        文字数は90語以上、110語未満です。pythonを使って文字数を数えて、
        指定の文字数範囲に収まるまで生成を繰り返してください
        以下のユーザー情報に基づき、5年後の幸せな「家族の日常ストーリー」を生成してください。
        ユーザーが「子どもを持つ未来も悪くないな」とポジティブになれるような、温かい内容にしてください。
        
        # ユーザー情報
        - 年齢: {age}歳
        - 収入レンジ: {income_range}
        - 居住地: {area}
        - 趣味: {hobby}

        # 生成するストーリー（300文字程度）:
        """
        
        # AIに「未来の手紙」を作ってもらうための指示書
        letter_prompt = f"""
        あなたは、未来（5年後）に生まれた子ども（5歳）の視点になりきってください。
        以下のユーザー情報を持つ未来の「パパ」または「ママ」に向けて、愛情のこもった短い「未来の手紙」を生成してください。
        子どもらしい、少し拙い（つたない）言葉遣いで書いてください。

        # ユーザー情報
        - 年齢: {age}歳
        - 居住地: {area}
        - 趣味: {hobby}

        # 生成する手紙（100文字程度）:
        """

        # Gemini AIを呼び出して、ストーリーと手紙を「同時」に生成させる
        # （model.start_chat() を使って会話形式で依頼します）
        chat = model.start_chat()
        
        response_story = chat.send_message(story_prompt)
        story_text = response_story.text

        response_letter = chat.send_message(letter_prompt)
        letter_text = response_letter.text

        print("--- AIからの応答（ストーリー） ---")
        print(story_text)
        print("--- AIからの応答（手紙） ---")
        print(letter_text)

        # --- 6. AIの答えをフロントエンドに返す ---
        ai_response = {
            "id": f"sim-{age}-{area}",
            "story": story_text,
            "imageUrl": "https://via.placeholder.com/600x400.png?text=Family+Illustration", # (画像生成は次のステップ)
            "letter": letter_text,
            "imagePrompt": "A dummy image prompt.", # (これもAIに作らせるとGood)
            "createdAt": "2025-10-21T10:45:00Z" # (本当は現在時刻を入れる)
        }
        
        return jsonify(ai_response)

    except Exception as e:
        # もしAI呼び出しなどでエラーが起きたら、エラー内容をターミナルに出力
        print(f"!!! エラー発生: {e}")
        # フロントエンドには「サーバーエラー」を返す
        return jsonify({"error": {"message": str(e)}}), 500


# このファイルが「実行」されたときに、
# サーバーを起動するためのおまじないです。
if __name__ == "__main__":
    app.run(debug=True, port=8000)