FROM python:3.11-slim
# Create app user
RUN groupadd -r app && useradd -r -g app app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chown -R app:app /app
USER app
ENV FLASK_APP=app.py
# Use gunicorn for production-like server; bind to 0.0.0.0:5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
