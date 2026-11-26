# Imagem do painel (Next.js), em três fases. Só a última vai para a imagem final.

# 1. Instala as dependências (camada reutilizada enquanto o package-lock.json não mudar)
FROM node:22-alpine AS dependencias
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# 2. Compila o painel
FROM node:22-alpine AS compilar
WORKDIR /app
COPY --from=dependencias /app/node_modules ./node_modules
COPY . .
# O endereço da API visto do browser fica escrito no código na altura do build (NEXT_PUBLIC_).
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# 3. A imagem final: só o que é preciso para correr
FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000
COPY --from=compilar /app/package.json ./
COPY --from=compilar /app/node_modules ./node_modules
COPY --from=compilar /app/.next ./.next
COPY --from=compilar /app/public ./public
COPY --from=compilar /app/next.config.ts ./
# a imagem "node" já traz um utilizador sem privilégios chamado node
USER node
EXPOSE 3000
CMD ["npm", "run", "start"]
