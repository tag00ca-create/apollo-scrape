# Use Apify's Python image with Chrome
FROM apify/actor-python-selenium:3.11

# Copy all files
COPY . ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the actor
CMD ["python", "__main__.py"]

