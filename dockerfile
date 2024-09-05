FROM python:3-slim
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY job.py /app/jobs.py
CMD [ "python", "/app/jobs.py"]