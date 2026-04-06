import httpx
from typing import Optional
from dataclasses import dataclass


OFF_BASE_URL = "https://world.openfoodfacts.org/api/v2/product"
OFF_HEADERS = {"User-Agent": "PrecioJusto/1.0 (contacto@preciojusto.ar)"}


@dataclass
class OffProductData:
    name: str
    brand: Optional[str]
    presentation: Optional[str]
    category: Optional[str]
    image_url: Optional[str]
    barcode: str


def _parse_product(barcode: str, product: dict) -> OffProductData:
    name = (
        product.get("product_name_es")
        or product.get("product_name")
        or product.get("abbreviated_product_name")
        or ""
    ).strip()

    brand = (product.get("brands") or "").split(",")[0].strip() or None

    presentation = (product.get("quantity") or "").strip() or None

    raw_categories = product.get("categories_tags") or []
    category = None
    for tag in raw_categories:
        if tag.startswith("es:"):
            category = tag.replace("es:", "").replace("-", " ").title()
            break
    if not category and raw_categories:
        last = raw_categories[-1]
        category = last.split(":")[-1].replace("-", " ").title()

    image_url = (
        product.get("image_front_url")
        or product.get("image_url")
        or None
    )

    return OffProductData(
        name=name,
        brand=brand,
        presentation=presentation,
        category=category,
        image_url=image_url,
        barcode=barcode,
    )


async def lookup_barcode(barcode: str) -> Optional[OffProductData]:
    url = f"{OFF_BASE_URL}/{barcode}.json"
    params = {"fields": "product_name,product_name_es,brands,quantity,categories_tags,image_front_url,image_url"}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params, headers=OFF_HEADERS)

        if response.status_code != 200:
            return None

        data = response.json()

        if data.get("status") != 1:
            return None

        product = data.get("product", {})
        parsed = _parse_product(barcode, product)

        if not parsed.name:
            return None

        return parsed

    except (httpx.RequestError, httpx.TimeoutException, ValueError):
        return None
