import os
import uuid

from azure.storage.blob import BlobServiceClient
from fastapi import File


class AzureBlobService:
    CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "")

    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(AzureBlobService.CONNECTION_STRING)

    def subir_arquivo(self, file: File, filename: str):
        try:
            extensao = filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{extensao}"

            blob_client = self.blob_service_client.get_blob_client(container=AzureBlobService.CONTAINER_NAME, blob=filename)
            blob_client.upload_blob(file, overwrite=True)

            return f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{AzureBlobService.CONTAINER_NAME}/{filename}", filename
        except Exception as e:
            print(f"Erro ao fazer upload: {e}")
            return None, None

    def excluir_arquivo(self, filename: str):
        try:
            blob_client = self.blob_service_client.get_blob_client(container=AzureBlobService.CONTAINER_NAME, blob=filename)
            blob_client.delete_blob()
            return True
        except Exception as e:
            print(f"Erro ao fazer upload: {e}")
            return False
