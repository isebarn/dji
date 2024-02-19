import requests
from bs4 import BeautifulSoup
import pandas as pd


def get_urls():
    # URL of the sitemap
    sitemap_url = "https://assets.djicdn.com/sitemap/store/store-nl.xml"

    # Send a GET request to the sitemap URL
    response = requests.get(sitemap_url)

    # Parse the XML content of the sitemap
    soup = BeautifulSoup(response.content, "xml")

    # Find all <loc> tags and store their text content (URLs) in a list
    urls = [url.text for url in soup.find_all("loc")]

    # Convert the list of URLs into a DataFrame
    urls_df = pd.DataFrame(urls, columns=["URLs"])

    # Save the DataFrame to an Excel file
    urls_df.to_excel("urls.xlsx", index=False)


def get_marked_urls():
    # Load the spreadsheet
    urls_df = pd.read_excel("urls.xlsx")

    # Filter rows where the second column has 'x'
    marked_urls_df = urls_df[urls_df.iloc[:, 1] == "x"]

    # Return the filtered URLs
    return marked_urls_df["URLs"].tolist()


def scrape_url(url):
    # Send a GET request to the URL
    response = requests.get(url)

    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the <h1> tag with a class that partially matches "style__product-title" and get its text content
    product_title = soup.find(
        "h1", class_=lambda x: x and "style__product-title" in x
    ).text

    # Find the <span> tag with a class that partially matches "style__price" and get its text content
    product_price = (
        soup.find("span", class_=lambda x: x and "style__price" in x)
        .text.strip()
        .replace("€", "")
    )

    # Find the <meta> tag with the name 'ean' and get its 'content' attribute value
    product_ean = soup.find("meta", attrs={"name": "ean"})["content"]

    # Find all <li> tags within an unordered list with a class that partially matches "eventBenefitItem__event" and get their text content
    event_benefits = [
        li.text.strip()
        for li in soup.find_all(
            "ul", class_=lambda x: x and "eventBenefitItem__event" in x
        )
    ]

    # Find the div with the class 'slick-track' and retrieve all <a> tags with the class 'presentation'
    presentation_urls = [
        a.find("img")["src"] for a in soup.find_all("a", role="presentation")
    ]

    # Find all <span> tags with the class 'lazyload-wrapper', then find the <img> within each and get the 'src' attribute
    lazyload_img_urls = [
        span  # span.find("div").find("img")["src"]
        for span in soup.find_all("span", class_="lazyload-wrapper")
    ]
    print(lazyload_img_urls)

    # Return the product title, price, EAN, event benefits, presentation URLs, and lazyload image URLs
    return (
        product_title,
        product_price,
        product_ean,
        event_benefits,
        presentation_urls,
        lazyload_img_urls,
    )


get_urls()