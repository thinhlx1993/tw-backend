# Use a base image with Python pre-installed
FROM python:3.10.5

# Set environment variables (optional)
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY dev-requirements.txt dev-requirements.txt

RUN apt-get update && apt-get -y install \
    libssl-dev \
    libffi-dev \
    libsasl2-dev \
    libldap2-dev \
    uwsgi

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r dev-requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose port 5000 for the Flask app
EXPOSE 8080

# Start uWSGI with the Flask app
#CMD ["uwsgi", "--ini", "/app/uwsgi.ini"]
CMD ["python", "run.py"]
