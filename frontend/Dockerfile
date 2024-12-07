# dockerfile for flask frontend
# the frontend project will be mounted to the container

FROM python:3.10-slim

# set the working directory
WORKDIR /app

# copy the requirements file
COPY requirements.txt .

# install the requirements
RUN pip install -r requirements.txt

# copy the frontend project
COPY . .

# expose the port
EXPOSE 5000

# run the flask app
CMD ["flask", "run", "--host=0.0.0.0"]