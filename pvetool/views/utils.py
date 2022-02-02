import logging

import boto3
import botocore
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy

from app.models import Client
from project.models import Project

from project.models import BijlageToAnnotation
from pvetool.models import BijlageToReply

from utils.writeExcelProject import WriteExcelProject

@login_required(login_url="login_syn")
def DownloadAnnotationAttachment(request, client_pk, projid, annid, attachment_id):    
    if annid != 0:
        item = BijlageToAnnotation.objects.filter(
            ann__project__id=projid, ann__id=annid, id=attachment_id
        ).first()
    else:
        item = BijlageToAnnotation.objects.filter(
            id=attachment_id
        ).first()
    expiration = 10000
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=botocore.client.Config(
            signature_version=settings.AWS_S3_SIGNATURE_VERSION
        ),
    )
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": str(item.attachment)},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return HttpResponseRedirect(response)


def GetAWSURL(client):
    expiration = 10000
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=botocore.client.Config(
            signature_version=settings.AWS_S3_SIGNATURE_VERSION
        ),
    )
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": str(client.logo)},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response


@login_required
def DownloadReplyAttachment(request, client_pk, pk, reply_id, attachment_id):
    item = BijlageToReply.objects.filter(reply__id=reply_id, id=attachment_id).first()
    
    expiration = 10000
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=botocore.client.Config(
            signature_version=settings.AWS_S3_SIGNATURE_VERSION
        ),
    )

    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": str(item.attachment)},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return HttpResponseRedirect(response)

@login_required(login_url=reverse_lazy("logout"))
def DownloadExcelProject(request, client_pk, pk):
    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    if not Project.objects.filter(pk=pk).exists():
        return redirect("logout_syn", client_pk=client_pk)
    
    project = Project.objects.get(pk=pk)
    client = project.client
    
    if client.logo:
        logo_obj = client.logo
        

    worksheet = WriteExcelProject()
    excelFilename = worksheet.linewriter(project, logo_obj)
    excelFilename = f"/{excelFilename}.xlsx"

    fl_path = settings.EXPORTS_ROOT
    try:
        fl = open(fl_path + excelFilename, "rb")
    except OSError:
        raise Http404("404")

    response = HttpResponse(
        fl,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = "inline; filename=%s" % excelFilename

    return response
