# Use lightweight Python image
FROM python:3.13-slim

# Copy and install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Start Flask
EXPOSE 8080
CMD ["python", "RunAndBunStats.py"]