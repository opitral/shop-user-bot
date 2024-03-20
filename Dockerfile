FROM python:latest
WORKDIR app/
COPY src/ .
RUN pip install -r requirements.txt
CMD ["python", "bot.py"]
