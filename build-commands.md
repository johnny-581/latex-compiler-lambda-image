aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 838220668044.dkr.ecr.us-east-1.amazonaws.com

docker buildx build --platform linux/amd64 -t latex-compiler-lambda --load . 

docker tag latex-compiler-lambda:latest 838220668044.dkr.ecr.us-east-1.amazonaws.com/latex-compiler-lambda:latest

docker push 838220668044.dkr.ecr.us-east-1.amazonaws.com/latex-compiler-lambda:latest