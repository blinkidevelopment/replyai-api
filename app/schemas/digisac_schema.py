from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime


class MessageData(BaseModel):
    ack: int
    isNew: bool
    isFirst: bool

class Message(BaseModel):
    id: str
    isFromMe: bool
    sent: bool
    type: str
    timestamp: datetime
    data: MessageData
    visible: bool
    accountId: str
    contactId: str
    fromId: Optional[str]
    serviceId: str
    toId: Optional[str]
    userId: Optional[str]
    ticketId: str
    ticketUserId: Optional[str]
    ticketDepartmentId: Optional[str]
    quotedMessageId: Optional[str]
    origin: Optional[str]
    createdAt: datetime
    updatedAt: datetime
    deletedAt: Optional[datetime]
    hsmId: Optional[str]
    isComment: bool
    reactionParentMessageId: Optional[str]
    isTranscribing: Optional[bool]
    transcribeError: Optional[str]
    text: Optional[str] = None
    obfuscated: bool
    file: Optional[Union[str, dict]]
    files: Optional[Union[List[str], List[dict]]]
    quotedMessage: Optional[dict]
    isFromBot: bool

class Data(BaseModel):
    id: str
    contactId: str
    serviceId: str
    accountId: str
    command: str
    message: Message

class DigisacRequest(BaseModel):
    event: str
    data: Data
    webhookId: str
    timestamp: datetime
