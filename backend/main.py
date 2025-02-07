import os
import logging
import random
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

import openai
from google import genai

# ===============================
# 環境変数やモデル名
# ===============================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GPT_MODEL_NAME = "chatgpt-4o-latest"
GEMINI_MODEL_NAME = "gemini-2.0-flash"

openai.api_key = OPENAI_API_KEY

client = None
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Geminiの初期化エラー: {e}")

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_server")


# ===============================
# GPT 呼び出し関数
# ===============================
def call_chatgpt(prompt: str) -> str:
    response = openai.chat.completions.create(
        model=GPT_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content


# ===============================
# Gemini 呼び出し関数
# ===============================
def call_gemini(prompt: str) -> str:
    if not client:
        raise RuntimeError("GeminiのClientが初期化されていません")
    response = client.models.generate_content(
        model=GEMINI_MODEL_NAME,
        contents=prompt,
    )
    return response.text


@app.get("/")
async def index():
    return HTMLResponse("<h1>GPT x Gemini - 最低3回、最大10回、合意で終了、詳細まとめ</h1>")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    - 両者が最低3回は話す
    - 各モデル最大10回 (合計20発言) になったら強制終了
    - それまでに"合意" or "同意" が出ても、両者とも3回以上話していなければ続行
    - まとめは、実際の会話履歴を参照して bullet points で作成
    """
    await websocket.accept()
    logger.info("クライアントが接続されました")

    try:
        while True:  # ユーザー入力を複数回受け付けたい場合
            conversation_history = []  # (sender, text)
            user_input = await websocket.receive_text()
            logger.info(f"ユーザー入力: {user_input}")

            # ユーザーの議題を保存
            conversation_history.append(("User", user_input))

            # (1) GPT / Gemini 初期見解
            try:
                gpt_first = call_chatgpt(
                    f"""議題: '{user_input}' に対して建設的な初見を述べてください。
                    攻撃的ではなく、補足や提案、結論に向かうアイデアを示してほしい。500文字以内でお願いします。"""
                )
            except Exception as e:
                err_msg = f"ChatGPTエラー: {e}"
                await websocket.send_text(json.dumps({"sender": "system", "text": err_msg}))
                break

            try:
                gemini_first = call_gemini(
                    f"""議題: '{user_input}' に対して建設的な初見を述べてください。
                    攻撃的ではなく、補足や提案、結論に向かうアイデアを示してほしい。。500文字以内でお願いします。"""
                )
            except Exception as e:
                err_msg = f"Geminiエラー: {e}"
                await websocket.send_text(json.dumps({"sender": "system", "text": err_msg}))
                break

            # 初期発言を送信 & 履歴保存
            await websocket.send_text(json.dumps({
                "sender": f"GPT({GPT_MODEL_NAME})",
                "text": gpt_first
            }))
            conversation_history.append((f"GPT({GPT_MODEL_NAME})", gpt_first))

            await websocket.send_text(json.dumps({
                "sender": f"Gemini({GEMINI_MODEL_NAME})",
                "text": gemini_first
            }))
            conversation_history.append((f"Gemini({GEMINI_MODEL_NAME})", gemini_first))

            # 発言カウント
            gpt_count = 1  # GPTが1回話した
            gem_count = 1  # Geminiが1回話した

            # (2) ランダム先攻/後攻 (この議題中は固定)
            roles = [f"GPT({GPT_MODEL_NAME})", f"Gemini({GEMINI_MODEL_NAME})"]
            random.shuffle(roles)
            attacker = roles[0]
            defender = roles[1]

            attacker_opinion = gpt_first if "GPT" in attacker else gemini_first
            defender_opinion = gpt_first if "GPT" in defender else gemini_first

            concluded = False

            max_comments = 10

            while True:
                # attacker発言
                attacker_prompt = f"""
                あなたは {attacker} として議論に参加しています。
                相手({defender})の意見:
                {defender_opinion}

                攻撃的ではなく建設的に反論や補足を行い、
                合意が得られそうなら合意を示してください。
                疑問点や矛盾点があれば質問し、回答を求めてください。
                (最終的に合意や結論が得られるように努めてください。)
                。500文字以内でお願いします。
                あなたの発言回数が既に {gpt_count if "GPT" in attacker else gem_count} 回目です。
                発言回数は{max_comments}です。上限に近づくにつれて意見が収束するようにしてください。
                """
                try:
                    if "GPT" in attacker:
                        # GPT
                        if gpt_count >= 10:
                            # 10回を超えるなら終了
                            logger.info("GPTが10回に到達 => 議論打ち切り")
                            break
                        attacker_resp = call_chatgpt(attacker_prompt)
                    else:
                        # Gemini
                        if gem_count >= 10:
                            logger.info("Geminiが10回に到達 => 議論打ち切り")
                            break
                        attacker_resp = call_gemini(attacker_prompt)

                except Exception as e:
                    err_msg = str(e)
                    await websocket.send_text(json.dumps({"sender": "system", "text": err_msg}))
                    concluded = True
                    break

                # カウント + 履歴保存
                if "GPT" in attacker:
                    gpt_count += 1
                else:
                    gem_count += 1

                conversation_history.append((f"{attacker}(先攻)#{gpt_count if 'GPT' in attacker else gem_count}", attacker_resp))
                await websocket.send_text(json.dumps({
                    "sender": f"{attacker}(先攻)#{gpt_count if 'GPT' in attacker else gem_count}",
                    "text": attacker_resp
                }))

                # 合意判定
                # 両者が最低3回以上話していないときは合意判定無視
                if gpt_count >= 3 and gem_count >= 3:
                    if "合意" in attacker_resp or "同意" in attacker_resp:
                        logger.info("先攻で合意 => 議論終了")
                        concluded = True
                        break

                # 後攻発言
                defender_prompt = f"""
                あなたは {defender} として議論に参加しています。
                相手({attacker})の意見:
                {attacker_resp}

                攻撃的ではなく建設的に補足や訂正を行い、
                合意が得られそうなら合意を示してください。
                疑問点や矛盾点があれば質問し、回答を求めてください。
                。500文字以内でお願いします。
                あなたの発言回数が既に {gpt_count if "GPT" in defender else gem_count} 回目です。
                発言回数は{max_comments}です。上限に近づくにつれて意見が収束するようにしてください。
                """
                try:
                    if "GPT" in defender:
                        if gpt_count >= max_comments:
                            logger.info(f"GPTが{max_comments}回に到達 => 議論打ち切り")
                            break
                        defender_resp = call_chatgpt(defender_prompt)
                    else:
                        if gem_count >= max_comments:
                            logger.info(f"Geminiが{max_comments}回に到達 => 議論打ち切り")
                            break
                        defender_resp = call_gemini(defender_prompt)

                except Exception as e:
                    err_msg = str(e)
                    await websocket.send_text(json.dumps({"sender": "system", "text": err_msg}))
                    concluded = True
                    break

                if "GPT" in defender:
                    gpt_count += 1
                else:
                    gem_count += 1

                conversation_history.append((f"{defender}(後攻)#{gpt_count if 'GPT' in defender else gem_count}", defender_resp))
                await websocket.send_text(json.dumps({
                    "sender": f"{defender}(後攻)#{gpt_count if 'GPT' in defender else gem_count}",
                    "text": defender_resp
                }))

                if gpt_count >= 3 and gem_count >= 3:
                    if "合意" in defender_resp or "同意" in defender_resp:
                        logger.info("後攻で合意 => 議論終了")
                        concluded = True
                        break

                # 10回到達チェック
                if gpt_count >= max_comments or gem_count >= max_comments:
                    logger.info(f"どちらかが{max_comments}回発言に到達 => 終了")
                    break

                # 次の発話に備えて最新意見更新
                attacker_opinion = attacker_resp
                defender_opinion = defender_resp

            # 結論まとめ
            conversation_text = ""
            for (speaker, text) in conversation_history:
                conversation_text += f"{speaker}:\n{text}\n\n"

            summary_prompt = f"""
            あなたはこの議論全体を観察していたGPTです。

            これまでの議論ログ:
            \"\"\"
            {conversation_text}
            \"\"\"

            以下の形式で最終的な議論を要約してください:
            ただし、マークダウンで出力したいので改行などは適切に入れてください
            1. 【議題・テーマ】(bullet points)
            2. 【各発言者の主張と質問・回答】(bullet points)
            3. 【合意点 / 食い違い点】(bullet points)
            4. 【結論と今後の方向性】(bullet points)
            結論については最初の議題についての結論を求めます。論点を変えないでください。

            必ず bullet points を使い、具体的内容を踏まえてまとめてください。
            """
            try:
                final_summary = call_chatgpt(summary_prompt)
                conversation_history.append((f"GPTまとめ({GPT_MODEL_NAME})", final_summary))
                await websocket.send_text(json.dumps({
                    "sender": f"GPTまとめ({GPT_MODEL_NAME})",
                    "text": final_summary
                }))
            except Exception as e:
                err_msg = str(e)
                logger.error(err_msg)
                await websocket.send_text(json.dumps({"sender": "system", "text": err_msg}))

            # 次の議題へ
            # break  # 1回で終了なら

    except WebSocketDisconnect:
        logger.warning("クライアントが切断されました")
    except Exception as e:
        logger.error(f"サーバーエラー: {e}")
    finally:
        await websocket.close()
        logger.info("WebSocketコネクション終了")
