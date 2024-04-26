import asyncio
import json
import httpx


class Config:
    BASE_URL = "https://4lapy.ru"
    CATEGORY_ENDPOINT = "/api/v2/catalog/product/list/?"
    PRODUCT_INFO_ENDPOINT = "/api/v2/catalog/product/info-list/"
    HEADERS = {
        "Authorization": "Basic NGxhcHltb2JpbGU6eEo5dzFRMyhy",
    }
    SIGN = "f379eaf3c831b04de153469d1bec345e"


async def get_products(
    client: httpx.Client, category_id: int = 1, count: int = 10, page: int = 1
) -> dict:
    params = {
        "sort": "popular",
        "category_id": category_id,
        "count": count,
        "page": page,
        "sign": Config.SIGN,
    }
    url = Config.BASE_URL + Config.CATEGORY_ENDPOINT

    r = client.get(url, params=params)
    return r.json()["data"]


async def get_products_info(client: httpx.Client, products_ids: list[int]) -> dict:
    url = Config.BASE_URL + Config.PRODUCT_INFO_ENDPOINT
    data = {
        "sort": "popular",
        "sign": Config.SIGN,
    } | {f"offers[{i}]": product_id for i, product_id in enumerate(products_ids, 1)}

    r = client.post(url, data=data)
    return r.json()["data"]


async def get_products_with_info(
    client: httpx.Client, category_id: int = 1, page: int = 1, count: int = 10
) -> list[dict]:
    products = await get_products(
        client=client, category_id=category_id, page=page, count=count
    )
    products_ids = products["goods_ids"]
    products_info = await get_products_info(client=client, products_ids=products_ids)
    for i in range(len(products["goods"])):
        products["goods"][i]["info"] = products_info["products"][i]
    return products["goods"]


async def get_100_products(client: httpx.Client, category_id: int = 1) -> list[dict]:
    result = await get_products_with_info(
        client=client, count=100, category_id=category_id
    )
    return result


async def main() -> None:
    client = httpx.Client(headers=Config.HEADERS)
    while True:
        try:
            products = await get_100_products(client)
            break
        except httpx.ReadTimeout:
            print("Read timeout, retrying...")
    products_with_needed_info = []
    for product in products:
        prices = "No active price"
        for variant in product["info"]["variants"]:
            if variant["active"]:
                prices = variant["price"]
        products_with_needed_info.append(
            {
                "id": product["id"],
                "title": product["title"],
                "webpage": product["webpage"],
                "brand_name": product["brand_name"],
                "prices": prices,
            }
        )

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products_with_needed_info, f, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(main())
    print("Done")
