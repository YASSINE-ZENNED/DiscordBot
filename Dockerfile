# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

ENV ffmpeg=ffmpeg



# Install FFmpeg and any needed packages specified in requirements.txt
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container (if needed)
EXPOSE 80

# Run bot.py when the container launches
CMD ["python", "index.py"]