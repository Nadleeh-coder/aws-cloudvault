import boto3

AWS_PROFILE = "cloudvault"
BUCKET_NAME = "cloudvault-documents-dev01"
OBJECT_KEY = "documents/presigned-upload-test.txt"
CONTENT_TYPE = "text/plain"
EXPIRATION_SECONDS = 300


def generate_presigned_put_url():
    session = boto3.Session(profile_name=AWS_PROFILE)
    s3 = session.client("s3")

    return s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": OBJECT_KEY,
            "ContentType": CONTENT_TYPE,
        },
        ExpiresIn=EXPIRATION_SECONDS,
        HttpMethod="PUT",
    )


if __name__ == "__main__":
    url = generate_presigned_put_url()

    print("Presigned PUT URL generated successfully.")
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Object key: {OBJECT_KEY}")
    print(f"Expires in: {EXPIRATION_SECONDS} seconds")
    print()
    print(url)
