from bs4 import BeautifulSoup as BS
import asyncio
import aiohttp
import sqlite3
from fake_useragent import UserAgent


HEADERS = {"User-Agent": UserAgent().random}
BASE_URL = f"https://rozetka.com.ua/pivo-i-sidr/c4649190/"


async def main():
    num = 1
    pagination_list = ""
    pagination = ""

    while True:
        page = f"page={num}/"
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL + page, headers=HEADERS) as response:
                r = await aiohttp.StreamReader.read(response.content)
                soup = BS(r, "html.parser")

                if len(pagination_list) == 0:
                    pagination_list = soup.find(
                        "ul", {"class": "pagination__list"}
                    ).text.strip()
                    pagination = pagination_list[pagination_list.rfind(" ") + 1 :]

                items = soup.find_all(
                    "li",
                    {
                        "class": "catalog-grid__cell catalog-grid__cell_type_slim ng-star-inserted"
                    },
                )
                get_data_page(items)
                if num == int(pagination):
                    break
                num += 1


def get_data_page(items):
    for item in items:
        status = item.find(
            "div",
            {
                "class",
                "goods-tile__availability",
            },
        ).text.strip()

        title = item.find(
            "a",
            {"class": "goods-tile__heading ng-star-inserted"},
        )
        link = title.get("href")
        price = item.find("span", {"class": "goods-tile__price-value"})
        if price:
            price = price.text.strip()

        name, article = divide_title(title.text.strip())
        data_list: tuple = (name, article, price, status, link)

        save_db(data_list)


def divide_title(title: str):
    name = title[: title.rfind("(")]
    article = title[title.rfind("(") + 1 : title.rfind(")")]
    return name, article


def save_db(data: tuple):
    connect = sqlite3.connect("goods.sqlite3")
    cursor = connect.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS goods 
                                (name text, article text, price text, status text, link text)"""
    )
    cursor.execute(
        """INSERT OR IGNORE INTO goods VALUES (?,?,?,?,?)""",
        data,
    )
    connect.commit()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
