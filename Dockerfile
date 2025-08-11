# 1. Start from a modern Python base image. Python 3.9 is a great, stable choice for Lambda.
FROM python:3.9-slim-bullseye

# 2. Set the working directory
WORKDIR /var/task

# 3. Install build dependencies and LaTeX.
#    - We still need cmake and build-essential for awslambdaric.
#    - 'texlive-latex-base' provides the core LaTeX system.
#    - '--no-install-recommends' helps keep the image size smaller.
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    cmake \
    build-essential \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements and install Python dependencies.
#    The official Python image uses 'pip', not 'pip3', and it's already up-to-date.
COPY requirements.txt .
RUN pip install -r requirements.txt

# 5. Install the AWS Lambda Runtime Interface Client (RIC)
RUN pip install awslambdaric

# 6. Copy your Lambda handler code
COPY app.py .

# 7. Set the entrypoint to the Python RIC. Use 'python', not 'python3'.
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "app.handler" ]





# FROM blang/latex:ubuntu

# WORKDIR /var/task

# # Update package lists and install python3 and pip
# # The -y flag assumes "yes" to all prompts
# RUN apt-get update && apt-get install -y \
#     python3 \
#     python3-pip \
#     cmake \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# # update pip
# RUN python3 -m pip install --upgrade pip

# # Copy the requirements file and install Python dependencies
# COPY requirements.txt .
# RUN pip3 install -r requirements.txt

# # Install the AWS Lambda Runtime Interface Client (RIC)
# RUN pip3 install awslambdaric

# # Copy your Lambda handler code
# COPY app.py .

# # Set the entrypoint to the Python RIC and the command to your handler
# ENTRYPOINT [ "python3", "-m", "awslambdaric" ]
# CMD [ "app.handler" ]