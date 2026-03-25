FROM python:3.12-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

<<<<<<< HEAD
CMD sh -c "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"
=======
CMD sh -c "python -m streamlit run app.py --server.port=${PORT:-10000} --server.address=0.0.0.0 --browser.gatherUsageStats=false"
>>>>>>> 83b5fbc7dbeb6ec32e5e88ad0cb7cf612f29c6ce
