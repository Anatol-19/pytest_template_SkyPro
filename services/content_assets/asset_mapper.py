from services.content_assets.models import ActualAsset


def _path(value):
    if isinstance(value, dict):
        return value.get("path") or ""
    return ""


def _add_source_assets(assets, sources, source_group, asset_type, api_root):
    group = sources.get(source_group, {}) if isinstance(sources, dict) else {}
    for quality, meta in group.items():
        path = _path(meta)
        if path:
            assets.append(ActualAsset(asset_type, quality, path, f"{api_root}.{source_group}.{quality}.path"))


def map_actual_assets(item):
    assets = []

    sources = item.get("sources", {})
    _add_source_assets(assets, sources, "paid", "full", "sources")
    _add_source_assets(assets, sources, "free", "trailer", "sources")

    short_video = _path(item.get("shortVideo"))
    if short_video:
        assets.append(ActualAsset("short", "", short_video, "shortVideo.path"))

    free_thumbnail = _path(item.get("freeThumbnail"))
    if free_thumbnail:
        assets.append(ActualAsset("tiles", "free", free_thumbnail, "freeThumbnail.path"))

    paid_thumbnail = _path(item.get("paidThumbnail"))
    if paid_thumbnail:
        assets.append(ActualAsset("tiles", "paid", paid_thumbnail, "paidThumbnail.path"))

    preview_image = _path(item.get("previewImage"))
    if preview_image:
        assets.append(ActualAsset("cover", "preview", preview_image, "previewImage.path"))

    featured_image = _path(item.get("image"))
    if featured_image:
        assets.append(ActualAsset("cover", "featured", featured_image, "image.path"))

    mask = _path(item.get("mask"))
    if mask:
        assets.append(ActualAsset("mask", "", mask, "mask.path"))

    script = _path(item.get("script"))
    if script:
        assets.append(ActualAsset("script", "", script, "script.path"))

    return assets
