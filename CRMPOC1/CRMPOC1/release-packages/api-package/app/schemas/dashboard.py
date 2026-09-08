from pydantic import BaseModel


class ComplaintsSummary(BaseModel):
    pending: int
    resolved: int
    under_process: int
    rejected: int
    in_process: int


class InstallationSummary(BaseModel):
    total_pending: int
    gt7days: int
    gt15days: int
    gt30days: int


class ComplaintChartPoint(BaseModel):
    month: str
    pending: int
    resolved: int
    under_process: int
    rejected: int
    in_process: int


class ComplaintChart(BaseModel):
    points: list[ComplaintChartPoint]


class OrdersSummary(BaseModel):
    total: int
    pending: int
    in_transit: int
    delivered: int
