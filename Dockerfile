FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Example: generate a plan on container start.
# Override CMD at `docker run` time to pass your own --occasion/--guests/--budget.
ENTRYPOINT ["python", "-m", "src.cli"]
CMD ["plan", "--occasion", "30th birthday", "--guests", "20", "--budget", "500", "--style", "outdoor"]
