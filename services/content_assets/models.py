from dataclasses import dataclass


@dataclass(frozen=True)
class ExpectedAsset:
    record_no: int
    title: str
    slug: str
    asset_type: str
    quality: str
    expected_path: str
    source_column: str


@dataclass(frozen=True)
class ActualAsset:
    asset_type: str
    quality: str
    signed_url: str
    api_field: str


@dataclass
class VerificationResult:
    record_no: int
    title: str
    slug: str
    asset_type: str
    quality: str
    source_column: str
    expected_path: str
    api_field: str = ""
    signed_url: str = ""
    ttl: str = ""
    token_present: bool = False
    api_status: str = "ok"
    cdn_status: str = ""
    verification_status: str = "pending"
    details: str = ""
