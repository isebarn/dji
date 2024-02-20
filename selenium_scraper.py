from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pandas import read_excel, DataFrame
from time import sleep


def start_driver():
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    print("testing started")
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver


def write_data_to_excel(scraped_data):
    # Check if data.xlsx exists, if not create it with appropriate headers
    try:
        output_df = read_excel("data.xlsx")
    except FileNotFoundError:
        output_df = DataFrame(
            columns=[
                "title",
                "price",
                "product_url",
                "ean",
                "highlights",
                "main_image_urls",
                "description_images",
                "description_text_title",
                "description_text",
                "box_images",
                "box_descriptions",
                "questions",
                "answers",
                "closer_look_name",
                "closer_look_value",
            ]
        )

    # Append the scraped data to the dataframe
    output_df = output_df._append(scraped_data, ignore_index=True)

    # Save the updated dataframe to data.xlsx
    output_df.to_excel("data.xlsx", index=False)


def get_marked_urls():
    # Load the spreadsheet
    urls_df = read_excel("urls.xlsx")

    # Filter rows where the second column has 'x'
    marked_urls_df = urls_df[urls_df.iloc[:, 1] != "x"]

    # Return the filtered URLs
    return marked_urls_df["URLs"].tolist()


def get_title(driver):
    title_element = driver.find_element(By.TAG_NAME, "h1")
    return title_element.text


def get_price(driver):
    price_element = driver.find_element(By.CSS_SELECTOR, "[class*='style__price']")
    return price_element.text.replace(" ", "").replace("€", "")


def get_ean(driver):
    ean_element = driver.find_element(By.XPATH, "//meta[@name='ean']")
    return ean_element.get_attribute("content").replace("EAN", "")


def get_highlights(driver):
    event_benefit_ul = driver.find_elements(
        By.CSS_SELECTOR, "ul[class*='eventBenefitItem__event-benefit']"
    )[1]
    event_benefit_items = event_benefit_ul.find_elements(By.TAG_NAME, "li")
    return [item.text for item in event_benefit_items]


def get_main_image_urls(driver):
    image_elements = driver.find_elements(
        By.CSS_SELECTOR, "a[role='presentation'] > img"
    )
    return [img.get_attribute("src") for img in image_elements]


def get_description_images(driver):
    take_a_closer_look_h3 = driver.find_element(
        By.XPATH, "//h3[text()='Take a Closer Look']"
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", take_a_closer_look_h3)
    img_box_divs = driver.find_elements(
        By.CSS_SELECTOR, "div[class*='index__img-box'] > img"
    )
    return [img.get_attribute("src") for img in img_box_divs]


def get_img_box_data(driver):
    img_box_titles = driver.find_elements(
        By.CSS_SELECTOR, "div[class*='index__desc__'] > h4"
    )
    titles = [title.text for title in img_box_titles]

    img_box_descriptions = driver.find_elements(
        By.CSS_SELECTOR, "div[class*='index__desc__'] > p"
    )
    descriptions = [description.text for description in img_box_descriptions]

    return titles, descriptions


def get_in_the_box_data(driver):
    box_images = []
    box_descriptions = []

    in_the_box_h3 = driver.find_element(By.XPATH, "//h3[text()='In the Box']")
    driver.execute_script("arguments[0].scrollIntoView(true);", in_the_box_h3)

    items = driver.find_elements(
        By.CSS_SELECTOR, "li[data-test-locator='sectionInTheBoxItem']"
    )

    for item in items:
        img_src = item.find_element(
            By.CSS_SELECTOR, "div:nth-child(1) > span > img"
        ).get_attribute("src")
        box_images.append(img_src)

        text = item.find_element(By.CSS_SELECTOR, "div:nth-child(2) > p").text
        box_descriptions.append(text)

    return box_images, box_descriptions


def get_QA(driver):
    qa = driver.find_element(By.XPATH, "//h3[text()='Let’s Answer Your Questions']")
    driver.execute_script("arguments[0].scrollIntoView(true);", qa)

    # Find the FAQ section using a partial match for the class name to avoid dynamic class name issues
    faq_section = driver.find_elements(
        By.XPATH, "//section[contains(@class, 'faq')]//li"
    )

    # Initialize an empty list to hold question-answer pairs
    qa_pairs = []

    # Iterate through each FAQ item
    for faq in faq_section:
        # Click the button next to the h5 to reveal the answer
        button = faq.find_element(By.CSS_SELECTOR, "h5 > span")
        driver.execute_script("arguments[0].click();", button)

        # Extract the question text using a more generic selector
        question = faq.find_element(By.CSS_SELECTOR, "h5 > span").text

        # Extract the answer text using a more generic selector
        answer = faq.find_element(By.CSS_SELECTOR, "article").text

        # Append the question-answer pair to the list
        qa_pairs.append({"question": question, "answer": answer})

    return qa_pairs


def get_closer_look(driver):
    closer_look_data = {}
    specs_rows = driver.find_elements(
        By.CSS_SELECTOR, ".temp-specs-tbody .temp-specs-tr"
    )
    for row in specs_rows:
        name = row.find_element(By.CSS_SELECTOR, ".temp-specs-td.name").text
        value = row.find_element(By.CSS_SELECTOR, ".temp-specs-td.value").text
        closer_look_data[name] = value
    return closer_look_data


# method to write error and url to a file errors.txt
def write_error_to_file(url, error):
    with open("errors.txt", "a", encoding="utf-8") as file:
        file.write(f"URL: {url}\nError: {error}\n\n")


def run_method(method, driver):
    try:
        return method(driver)
    except Exception as e:
        write_error_to_file(driver.current_url, e)
        return None


def scrape_url(url, driver):
    driver.get(url)
    sleep(1)

    title = run_method(get_title, driver)
    price = run_method(get_price, driver)
    ean = run_method(get_ean, driver)
    highlights = run_method(get_highlights, driver)
    main_image_urls = run_method(get_main_image_urls, driver)

    description_images = run_method(get_description_images, driver)
    img_box_data = run_method(get_img_box_data, driver)
    if img_box_data is not None:
        description_text_title, description_text = img_box_data
    else:
        description_text_title, description_text = None, None

    box_data = run_method(get_in_the_box_data, driver)
    if box_data is not None:
        box_images, box_descriptions = box_data
    else:
        box_images, box_descriptions = None, None

    qa_pairs = run_method(get_QA, driver)

    if qa_pairs:
        questions = [pair["question"] for pair in qa_pairs]
        answers = [pair["answer"] for pair in qa_pairs]
    else:
        questions, answers = None, None

    closer_look_data = run_method(get_closer_look, driver)
    if closer_look_data:
        closer_look_name = [key for key in closer_look_data.keys()]
        closer_look_value = [value for value in closer_look_data.values()]
    else:
        closer_look_name, closer_look_value = None, None

    # with open("page.html", "w", encoding="utf-8") as file:
    #    file.write(driver.page_source)
    # input("Press Enter after you're done inspecting the page...")

    return {
        "title": title,
        "price": price,
        "product_url": url,
        "ean": ean,
        "highlights": highlights,
        "main_image_urls": main_image_urls,
        "description_images": description_images,
        "description_text_title": description_text_title,
        "description_text": description_text,
        "box_images": box_images,
        "box_descriptions": box_descriptions,
        "questions": questions,
        "answers": answers,
        "closer_look_name": closer_look_name,
        "closer_look_value": closer_look_value,
    }


def run():
    driver = start_driver()
    urls = get_marked_urls()
    # urls = [
    #    "https://store.dji.com/pt/product/dji-mavic-3e-and-dji-care-enterprise-basic"
    # ]
    for url in urls:
        scraped_data = scrape_url(url, driver)
        write_data_to_excel(scraped_data)


run()
