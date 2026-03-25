
import boto3
from dotenv import load_dotenv
import os

load_dotenv()
print("This is loaddot env", load_dotenv())
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID1"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY1"),
    region_name="us-east-2" 
    )



def get_s3_url(filename: str) -> str:
    
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": "ghazihussainnbucket1", "Key": f"rag_uploads/{filename}"},
        ExpiresIn=3600
    )
    return url

def upload_s3(file):
    print("uploading on s3 .....")
    s3.upload_fileobj(file.file, "ghazihussainnbucket1", f"rag_uploads/{file.filename}")
    print("Done")

def delete_file(filename):
    print("deleting file from s3 .....")
    s3.delete_object(Bucket="ghazihussainnbucket1", Key=f"rag_uploads/{filename}")
    print("Done")

def get_all_s3_files():
    response = s3.list_objects_v2(Bucket="ghazihussainnbucket1", Prefix="rag_uploads/")
    
    if "Contents" not in response:
        return []
    
    return [obj["Key"] for obj in response["Contents"]]

if __name__ == "__main__":
    print("Before files :--- ", get_all_s3_files())
    delete_file("sample2.txt")
    print("After files :--- ", get_all_s3_files())
