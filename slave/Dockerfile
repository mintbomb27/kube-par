FROM python:3.9

WORKDIR /app

ADD main.py .

RUN pip install flask python-dotenv requests

EXPOSE 8000

CMD ["python","main.py"]