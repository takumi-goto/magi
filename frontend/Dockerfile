FROM node:22
# `app/` の package.json を使用
COPY app/package.json app/package-lock.json ./app/
WORKDIR /app

# 依存関係をインストール
RUN npm install

# アプリのソースコードをコピー
COPY app/ ./app/

CMD ["npm", "run", "dev", "--", "--port", "3001"]
