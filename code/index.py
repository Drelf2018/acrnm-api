from dataclasses import dataclass, field
from typing import List

import cloudscraper
import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from lxml import etree

app = FastAPI()
scraper = cloudscraper.create_scraper()

@dataclass
class Variant:
    color: str
    size: str

@dataclass
class Product:
    name: str
    href: str
    price: str
    variants: List[Variant] = field(default_factory=list)


def get_page_root() -> etree._Element:
    resp = scraper.get("https://acrnm.com/index?sort=default&filter=txt").text
    return etree.HTML(resp)


def parse_products(root: etree._Element) -> List[Product]:
    products = []
    table: List[etree._Element] = root.cssselect(".m-product-table__row")
    for tr in table:
        price = tr.xpath("./td[4]/span/text()")
        if len(price) == 0:
            continue
        product = Product(tr.xpath("./td[1]/a/span/text()")[0], tr.xpath("./td[1]/a/@href")[0], price[0])
        variants: List[etree._Element] = tr.xpath("./td[3]/div/span")
        for var in variants:
            color = ", ".join(var.xpath("./div/span/text()"))
            size = ", ".join(var.xpath("./span/text()"))
            product.variants.append(Variant(color, size))
        products.append(product)
    return products


@app.get("/")
def index():
    root = get_page_root()
    products = parse_products(root)
    return products


@app.get("/favicon.ico")
def favicon():
    return FileResponse("favicon.ico")


@app.get("/image/{name}")
def get_view(name: str):
    resp = scraper.get(f"https://acrnm.com/{name}").text
    root: etree._Element = etree.HTML(resp)
    src = root.xpath("/html/body/div[1]/main/turbo-frame/div/div[2]/div[1]/img/@src")
    return src[0]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
