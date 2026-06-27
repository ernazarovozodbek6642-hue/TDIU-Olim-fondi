FROM python:3.11.15-slim

WORKDIR /app

RUN pip install pipenv

COPY Pipfile Pipfile.lock* ./

RUN pipenv install --system --deploy --ignore-pipfile || pipenv install --system

COPY . .

CMD ["python", "app.py"]
