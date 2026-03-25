FROM python:3.12-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD sh -c "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"