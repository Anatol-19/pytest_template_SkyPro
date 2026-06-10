from REST.base_client import BaseApiClient


class ContentClient:
    def __init__(self, api_client=None):
        self.api_client = api_client or BaseApiClient()

    def get_post(self, slug):
        self.api_client.set_origin_headers(referer_path=f"/{slug}/")
        path = self.api_client.route("content_post") + slug
        data = self.api_client.get_json(path=path)
        status = data.get("status", {})
        if status.get("code") != 1:
            raise RuntimeError(f"Content API returned bad status for {slug}: {status}")
        item = data.get("data", {}).get("item")
        if not item:
            raise RuntimeError(f"Content API response does not contain data.item for {slug}")
        return item
