from pydantic import BaseModel
from typing import Optional


class Discount(BaseModel):
    value: float
    limitDate: Optional[str]
    dueDateLimitDays: int
    type: str

class Fine(BaseModel):
    value: float
    type: str

class Interest(BaseModel):
    value: float
    type: str

class Payment(BaseModel):
    object: str
    id: str
    dateCreated: str
    customer: str
    installment: str
    paymentLink: Optional[str]
    value: float
    netValue: float
    originalValue: Optional[float]
    interestValue: Optional[float]
    description: str
    billingType: str
    canBePaidAfterDueDate: bool
    confirmedDate: str
    pixTransaction: Optional[str]
    status: str
    dueDate: str
    originalDueDate: str
    paymentDate: str
    clientPaymentDate: str
    installmentNumber: int
    invoiceUrl: str
    invoiceNumber: str
    externalReference: Optional[str]
    deleted: bool
    anticipated: bool
    anticipable: bool
    creditDate: str
    estimatedCreditDate: str
    transactionReceiptUrl: str
    nossoNumero: str
    bankSlipUrl: str
    lastInvoiceViewedDate: Optional[str]
    lastBankSlipViewedDate: Optional[str]
    discount: Discount
    fine: Fine
    interest: Interest
    postalService: bool
    custody: Optional[str]
    refunds: Optional[str]

class AsaasPaymentRequest(BaseModel):
    id: str
    event: str
    dateCreated: str
    payment: Payment