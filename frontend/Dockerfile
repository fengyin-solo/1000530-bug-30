FROM node:20-alpine
WORKDIR /srv/web
# 先拷依赖清单与锁文件，按锁定版本安装，保证构建产物可复现
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
