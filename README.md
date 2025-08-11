Of course. Here is a detailed, step-by-step guide to run the `blang/latex` Docker image on AWS Lambda.

This guide will walk you through creating a Python-based AWS Lambda function that uses a custom Docker container with a full LaTeX environment to compile LaTeX code into a PDF.

### **Prerequisites**

*   An AWS account with access to IAM, Amazon ECR, and AWS Lambda.
*   The AWS CLI installed and configured on your local machine.
*   Docker Desktop installed and running on your local machine.

### **Project Structure**

First, create a new directory for your project. Inside this directory, you will create the following files:

```
latex-lambda/
|-- app.py
|-- Dockerfile
|-- requirements.txt
|-- sample-event.json
```

---

### **Step 1: Create the Python Lambda Handler (`app.py`)**

This Python script will be the heart of your Lambda function. It will receive the LaTeX code, save it to a file, execute the `pdflatex` command to generate a PDF, and then upload the resulting PDF to an S3 bucket.

```python
# app.py
import os
import subprocess
import boto3
import base64
from botocore.exceptions import NoCredentialsError

# It's a good practice to use environment variables for bucket names
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
s3_client = boto3.client('s3')

def handler(event, context):
    """
    Lambda handler to compile a LaTeX string to a PDF and upload to S3.
    """
    try:
        # Get the LaTeX source from the invocation event
        latex_source = event.get('latex_source')
        if not latex_source:
            return {
                'statusCode': 400,
                'body': 'Error: Missing "latex_source" in the event payload.'
            }

        # The only writable directory in AWS Lambda is /tmp
        working_dir = '/tmp'
        tex_file_path = os.path.join(working_dir, 'document.tex')
        pdf_file_path = os.path.join(working_dir, 'document.pdf')
        output_filename = event.get('output_filename', 'output.pdf')

        # Write the LaTeX source to a .tex file
        with open(tex_file_path, 'w') as f:
            f.write(latex_source)

        # Run pdflatex command. We run it twice for cross-referencing.
        for _ in range(2):
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory=' + working_dir, tex_file_path],
                capture_output=True,
                text=True
            )

        if process.returncode != 0:
            return {
                'statusCode': 500,
                'body': f"LaTeX compilation failed. Error: {process.stderr}"
            }

        # Upload the generated PDF to S3
        if S3_BUCKET_NAME:
            try:
                s3_client.upload_file(pdf_file_path, S3_BUCKET_NAME, output_filename)
                return {
                    'statusCode': 200,
                    'body': f"Successfully compiled and uploaded {output_filename} to S3 bucket {S3_BUCKET_NAME}."
                }
            except NoCredentialsError:
                return {'statusCode': 500, 'body': 'S3 credentials not available.'}
            except Exception as e:
                return {'statusCode': 500, 'body': f"Error uploading to S3: {str(e)}"}
        else:
            # If no bucket is specified, return the PDF as a base64 encoded string
            with open(pdf_file_path, "rb") as pdf_file:
                encoded_string = base64.b64encode(pdf_file.read()).decode()
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/pdf',
                    'Content-Disposition': f'attachment; filename="{output_filename}"'
                },
                'body': encoded_string,
                'isBase64Encoded': True
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"An unexpected error occurred: {str(e)}"
        }

```

---

### **Step 2: Define Python Dependencies (`requirements.txt`)**

This file lists the Python packages that need to be installed in your Docker container. For this project, you'll need `boto3` to interact with AWS services.

```
boto3
```

---

### **Step 3: Create the Dockerfile**

The `Dockerfile` provides the instructions to build your custom container image. It starts with the `blang/latex` image, installs Python and the necessary dependencies, adds your handler code, and configures the entry point for AWS Lambda.

```dockerfile
# Use a specific version for reproducibility
FROM blang/latex:ubuntu

# Set the working directory
WORKDIR /var/task

# Update package lists and install python3 and pip
# The -y flag assumes "yes" to all prompts
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Install the AWS Lambda Runtime Interface Client (RIC)
RUN pip3 install awslambdaric

# Copy your Lambda handler code
COPY app.py .

# Set the entrypoint to the Python RIC and the command to your handler
ENTRYPOINT [ "python3", "-m", "awslambdaric" ]
CMD [ "app.handler" ]
```

---

### **Step 4: Build and Push the Docker Image to Amazon ECR**

Now, you will build the Docker image and push it to Amazon's container registry (ECR).

1.  **Create an ECR Repository:**
    Open your terminal and run the following command, replacing `your-region` and `your-repo-name` with your desired AWS region and repository name.
    ```bash
    aws ecr create-repository --repository-name your-repo-name --region your-region
    ```
    Make a note of the `repositoryUri` from the output.

2.  **Log in to ECR:**
    Authenticate your Docker client to your ECR registry.
    ```bash
    aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-aws-account-id.dkr.ecr.your-region.amazonaws.com
    ```
    Replace `your-aws-account-id` and `your-region`.

3.  **Build the Docker Image:**
    From your project directory, build the image.
    ```bash
    docker build -t your-repo-name .
    ```

4.  **Tag the Docker Image:**
    Tag the image with the ECR repository URI.
    ```bash
    docker tag your-repo-name:latest your-aws-account-id.dkr.ecr.your-region.amazonaws.com/your-repo-name:latest
    ```

5.  **Push the Image to ECR:**
    ```bash
    docker push your-aws-account-id.dkr.ecr.your-region.amazonaws.com/your-repo-name:latest
    ```

---

### **Step 5: Create the AWS Lambda Function**

1.  **Navigate to the Lambda Console:**
    Go to the AWS Lambda console and click "Create function".

2.  **Select "Container image":**
    *   For the function name, enter something descriptive like `latex-compiler`.
    *   For the **Container image URI**, click "Browse images" and select the repository and the `latest` tagged image you just pushed to ECR.
    *   Leave the **Architecture** as `x86_64`.

3.  **Configure Permissions:**
    *   Expand "Change default execution role".
    *   Choose "Create a new role with basic Lambda permissions".
    *   After the function is created, you will need to add permissions for S3. Go to the IAM console, find the newly created role, and attach the `AmazonS3FullAccess` policy (for simplicity in this tutorial; in a production environment, you should use a more restrictive policy).

4.  **Increase Memory and Timeout:**
    *   Go to the "Configuration" tab of your newly created Lambda function.
    *   Select "General configuration" and click "Edit".
    *   The `blang/latex` image is large, so increase the **Memory** to at least **2048 MB**.
    *   LaTeX compilation can be slow, especially on the first (cold) start. Increase the **Timeout** to **1 minute** or more.

5.  **(Optional) Add Environment Variable for S3 Bucket:**
    *   Under "Configuration" -> "Environment variables", add a new variable:
        *   **Key:** `S3_BUCKET_NAME`
        *   **Value:** `your-s3-bucket-name` (make sure this S3 bucket exists).

---

### **Step 6: Test Your Lambda Function**

1.  **Create a Test Event (`sample-event.json`):**
    Create a file named `sample-event.json` with the following content. This will be the input to your Lambda function.

    ```json
    {
      "output_filename": "hello-world.pdf",
      "latex_source": "\\documentclass{article}\\begin{document}Hello, World from AWS Lambda and Docker!\\end{document}"
    }
    ```

2.  **Invoke the Function:**
    *   In the Lambda console for your function, go to the "Test" tab.
    *   Paste the content of `sample-event.json` into the event JSON editor.
    *   Click "Test".

The first invocation will be slower due to the "cold start" (downloading the container image). Subsequent invocations will be much faster.

If everything is configured correctly, you should see a success message in the execution results, and the `hello-world.pdf` file will appear in your S3 bucket. If you didn't configure an S3 bucket, the response body will contain the base64-encoded PDF.