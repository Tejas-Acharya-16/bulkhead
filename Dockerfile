FROM python:3.12-slim
WORKDIR /app
COPY bulkhead ./bulkhead
COPY data ./data
COPY public ./public
COPY server.py ./
ENV PORT=8000
EXPOSE 8000
USER nobody
CMD ["python", "server.py"]
