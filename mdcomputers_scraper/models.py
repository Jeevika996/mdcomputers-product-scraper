from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Product:
    name: str
    url: str
    price: Optional[float] = None
    old_price: Optional[float] = None
    discount_percent: Optional[float] = None
    currency: str = "INR"
    image_url: Optional[str] = None
    availability: Optional[str] = None
    rating: Optional[float] = None
    sku_or_model: Optional[str] = None
    search_keyword: str = ""
    page_number: int = 1
    source_url: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def __post_init__(self):
        if self.name:
            self.name = " ".join(self.name.split())


if __name__ == "__main__":
    example_product = Product(
        name="MSI RTX 5060 Ventus 2X OC 8GB GDDR7 Graphics Card",
        url="https://www.mdcomputers.in/product/msi-rtx-5060-ventus-2x-oc-graphics-card-g5060-8v2c",
        price=46999.0,
        old_price=60999.0,
        discount_percent=22.94,
        currency="INR",
        image_url="https://mdcomputers.in/image/catalog/gpu1.webp",
        availability="In Stock",
        rating=4.5,
        sku_or_model="G5060-8V2C",
        search_keyword="rtx 5060",
        page_number=1,
        source_url="https://www.mdcomputers.in/?route=product/search&search=rtx+5060",
    )
    print(example_product.availability)
    print(example_product.price)
    print(example_product.name)