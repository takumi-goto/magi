import numpy as np
import matplotlib.pyplot as plt
import base64
from PIL import Image
import requests
from io import BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

class AnalyzeThumbnail:
    def __init__(self, thumbnail_url: str):
        self.thumbnail_url = thumbnail_url

    def analyze(self):
        """ 指定されたURLの画像を取得し、エッジ検出して縦横比を分析し、処理後の画像も返す """
        try:
            # ✅ 画像を取得
            response = requests.get(self.thumbnail_url, timeout=5)
            response.raise_for_status()  # HTTPエラー処理
            image = Image.open(BytesIO(response.content))
            image_array = np.array(image)

            # ✅ 明度を計算（RGBの平均を使用）
            brightness = np.mean(image_array, axis=2)  # RGBの平均を計算

            # ✅ 横方向（左右）の明暗変化を取得
            gradient_x = np.abs(np.diff(brightness, axis=1))  # 横方向の一次微分
            gradient_x_diff = np.abs(np.diff(gradient_x, axis=1))  # 横方向の二次微分

            # ✅ しきい値処理
            threshold = 50
            edges_x = (gradient_x_diff > threshold).astype(np.uint8) * 255

            # ✅ エッジ密度の計算
            edge_density_x = np.sum(edges_x, axis=0)  # 縦方向のエッジ密度（青線用）

            # ✅ ピーク検出の調整
            peak_threshold_x = np.max(edge_density_x) * 0.2  # 20% に変更
            peak_cols = np.where(edge_density_x > peak_threshold_x)[0]  # 縦方向のエッジ（青線用）

            # ✅ 左端・右端から中央へスキャン
            if len(peak_cols) > 1:
                min_x = int(peak_cols[0])  # 左端のエッジ
                max_x = int(peak_cols[-1])  # 右端のエッジ
                peak_cols = [min_x, max_x]  # 修正後のエッジ

            # ✅ 画像にラインを描画
            output_image = image_array.copy()

            # ✅ 青線（左右のエッジ検出）
            for col in peak_cols:
                output_image[:, col] = [255, 255, 0]  # 線を描画（左右ライン）

            # ✅ Matplotlib で画像を描画
            fig, ax = plt.subplots(figsize=(image_array.shape[1] / 100, image_array.shape[0] / 100))  # 元画像と同じ比率に調整
            ax.imshow(output_image, aspect='auto')
            ax.set_title("縦線を描画した画像")
            ax.axis("off")

            # ✅ Matplotlibの画像をBase64エンコード
            buffer = BytesIO()
            canvas = FigureCanvas(fig)
            canvas.print_png(buffer)
            buffer.seek(0)
            encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
            plt.close(fig)  # メモリ解放

            # ✅ 画像サイズ情報
            width, height = int(image_array.shape[1]), int(image_array.shape[0])

            # ✅ 縦横比の判定
            vertical_height = height
            vertical_width = max_x - min_x
            orientation = "縦長" if vertical_height > vertical_width else "横長"

            # ✅ **解析結果の出力（return はそのまま）**
            result = {
                "thumbnail_url": self.thumbnail_url,
                "width": width,
                "height": height,
                "vertical_height": int(vertical_height),
                "vertical_width": int(vertical_width),
                "orientation": orientation,
                "processed_image": f"data:image/png;base64,{encoded_image}"
            }

            print(f"解析結果: {result}")  # デバッグ用

            return result

        except requests.HTTPError as http_err:
            return {"error": f"HTTPエラー: {http_err}"}
        except Exception as err:
            return {"error": f"解析中にエラーが発生しました: {err}"}
