import logging
import os
import urllib
import zipfile

import boto3
import botocore
from app import models
from botocore.exceptions import ClientError
from django.conf import settings


class ZipMaker:
    def makeZip(self, zipFilename, filename, items):
        BASE = os.path.dirname(os.path.abspath(__file__))
        path = BASE + settings.EXPORTS_URL + zipFilename
        pdfPath = BASE + settings.EXPORTS_URL + filename + ".pdf"

        if not items:
            return False

        zipf = zipfile.ZipFile(f"{path}.zip", "w", zipfile.ZIP_DEFLATED)

        for item in items:
            # open attachment in AWS S3 server
            access_key = settings.AWS_ACCESS_KEY_ID
            secret_key = settings.AWS_SECRET_ACCESS_KEY
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            region = settings.AWS_S3_REGION_NAME
            signature = settings.AWS_S3_SIGNATURE_VERSION
            expiration = 10000
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
                config=botocore.client.Config(signature_version=signature),
            )
            try:
                response = s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket_name, "Key": str(item.attachment)},
                    ExpiresIn=expiration,
                )
            except ClientError as e:
                logging.error(e)
                return None

            page = urllib.request.urlopen(response)  # Change to website
            # put in this map of the zip with this name
            filename_split = str(item.attachment).split("/")
            map_name = filename_split[0]
            extension = filename_split[1].split(".")[1]
            if item.name:
                name = item.name
            else:
                name = filename_split[1].split(".")[0]
                
            full_attach_url = f"{map_name}/{name}.{extension}"
            zipf.writestr(full_attach_url, page.read())

        # write the pdf in the root of zip

        zipf.write(pdfPath, f"ProgrammaVanEisen.pdf")
        zipf.close()
        return True
