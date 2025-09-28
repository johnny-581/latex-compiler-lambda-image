import os
import subprocess
# import boto3
import base64
import uuid
# from dotenv import load_dotenv

# load_dotenv()

# S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
# s3_client = boto3.client('s3')

def handler(event, context):
    print("log log!!!")
    try:
        latex_source = event.get('latex_source')
        if not latex_source:
            return {
                'statusCode': 400,
                'body': 'Missing "latex_source" in the event payload!'
            }
        
        working_dir = '/tmp'
        unique_id = uuid.uuid4()

        base_filename = f'document_{unique_id}'
        tex_file_path = os.path.join(working_dir, f'{base_filename}.tex')
        pdf_file_path = os.path.join(working_dir, f'{base_filename}.pdf')
        log_path = os.path.join(working_dir, f'{base_filename}.log')
        
        with open(tex_file_path, 'w') as f:
            f.write(latex_source)

        for _ in range(2):
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode','-halt-on-error', '-file-line-error', '-output-directory=' + working_dir, tex_file_path],
                capture_output=True,
                text=True
            )

        print(f"[pdf-latex stdout head]\n{process.stdout[:1000]}")
        print(f"[pdf-latex stderr head]\n{process.stderr[:500]}")
        
        if process.returncode != 0:
            if os.path.exists(log_path):
                with open(log_path, 'r', errors="ignore") as log_file:
                    log_text = log_file.read()
                print("Latex compilation error!\n[pdf-latex log tail]\n" + log_text[-2000:])
            return {
                'statusCode': 500,
                'body': f"Latex compilation error: {process.stderr}"
            }

        # # upload to s3
        # try:
        #     s3_client.upload_file(pdf_file_path, S3_BUCKET_NAME, output_filename)
        #     return {
        #         'statusCode': 200,
        #         'body': f"Successfully compiled and uploaded to s3 bucket {S3_BUCKET_NAME}"
        #     }
        # except Exception as e:
        #     return {
        #         'statusCode': 500,
        #         'body': f"Error uploading to s3: {str(e)}"
        #     }

        with open(pdf_file_path, "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read()).decode()
        print(f"Successfully compiled to pdf!")
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/pdf'
            },
            'body': encoded_string,
            'isBase64Encoded': True
        }
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Unexpected error: {str(e)}"
        }