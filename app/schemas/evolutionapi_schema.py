from pydantic import BaseModel
from typing import Optional, List


class Key(BaseModel):
    remoteJid: str
    fromMe: bool
    id: str

class DeviceListMetadata(BaseModel):
    senderKeyHash: str
    senderTimestamp: str
    senderAccountType: str
    receiverAccountType: str
    recipientKeyHash: str
    recipientTimestamp: str

class MessageContextInfo(BaseModel):
    deviceListMetadata: DeviceListMetadata
    deviceListMetadataVersion: int
    messageSecret: str

class ImageMessage(BaseModel):
    url: str
    mimetype: str
    caption: str
    fileSha256: str
    fileLength: str
    height: int
    width: int
    mediaKey: str
    fileEncSha256: str
    directPath: str
    mediaKeyTimestamp: str
    jpegThumbnail: str
    firstScanSidecar: str
    firstScanLength: str
    scansSidecar: str
    scanLengths: List[int]
    midQualityFileSha256: str

class AudioMessage(BaseModel):
    url: str
    mimetype: str
    fileSha256: str
    fileLength: str
    seconds: int
    ptt: bool
    mediaKey: str
    fileEncSha256: str
    directPath: str
    mediaKeyTimestamp: str
    streamingSidecar: str
    waveform: Optional[str] = None

class Message(BaseModel):
    conversation: Optional[str] = None
    messageContextInfo: Optional[MessageContextInfo] = None
    imageMessage: Optional[ImageMessage] = None
    audioMessage: Optional[AudioMessage] = None
    base64: Optional[str] = None

class Data(BaseModel):
    key: Key
    pushName: str
    message: Message
    messageType: str
    messageTimestamp: int
    owner: str
    source: str

class EvolutionAPIRequest(BaseModel):
    event: str
    instance: str
    data: Data
    destination: str
    date_time: str
    sender: str
    server_url: str
    apikey: str