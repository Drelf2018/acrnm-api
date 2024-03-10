from dataclasses import dataclass, field
from typing import List

import cloudscraper
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from lxml import etree

app = FastAPI()
scraper = cloudscraper.create_scraper()

@dataclass
class Variant:
    color: List[str]
    size: List[str]

@dataclass
class Product:
    name: str
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
        product = Product(tr.xpath("./td[1]/a/span/text()")[0], price[0])
        variants: List[etree._Element] = tr.xpath("./td[3]/div/span")
        for var in variants:
            product.variants.append(
                Variant(var.xpath("./div/span/text()"), var.xpath("./span/text()")))
        products.append(product)
    return products


@app.get("/")
def _():
    root = get_page_root()
    products = parse_products(root)
    return products


@app.get("/favicon.ico")
def favicon():
    return FileResponse("favicon.ico")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
