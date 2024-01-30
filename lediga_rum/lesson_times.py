import numpy as np
import json
import pickle
import time
from multiprocessing.pool import ThreadPool as Pool
from datetime import datetime
from selenium import webdriver
from selenium.common import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

URL = "https://web.skola24.se/timetable/timetable-viewer/lund.skola24.se/Gymnasieskolan%20Spyken/"
BUTTON_XPATH = (
    "/html/body/div[3]/div[2]/div/div[2]/div[1]/div[1]/div[4]/div/div/button/i"
)
CLASSROOMS_XPATH = "/html/body/div[3]/div[2]/div/div[2]/div[1]/div[1]/div[4]/div/div/ul"
TIMETABLE_XPATH = (
    "/html/body/div[3]/div[2]/div/div[2]/div[2]/div//*[local-name() = 'svg']"
)
INCLUDED_CLASSROOMS = [
    "B01",
    "B12",
    "B31",
    "B32",
    "B33",
    "B34",
    "B35",
    "B40-grupprum",
    "B41",
    "B42",
    "B43",
    "C21",
    "C22",
    "C22-lilla",
    "C23",
    "C31",
    "C32",
    "C33",
    "C41",
    "C42",
    "C43",
    "D01",
    "D11",
    "D12",
    "D13 (Teatersal)",
    "D21",
    "D22",
    "D23",
    "D24",
    "D31",
    "D32",
    "D33",
    "D41",
    "D42",
    "D43",
    "F01",
    "F02",
    "F03",
    "F04",
    "F21",
    "F22",
    "F23",
    "F24",
    "F25",
    "F31 data",
    "F32 data",
    "F323",
    "F33 film",
    "G21 data",
    "G22",
    "G23",
    "G24 foto",
]
WEEK_BUTTON_XPATH = (
    "/html/body/div[3]/div[2]/div/div[2]/div[1]/div[2]/div/ul/li[1]/button"
)
POLL_INTERVAL = 0.5

SHOULD_UPDATE_ROOM_INDICES = False


def initialize_driver():
    service = Service(executable_path="/usr/bin/geckodriver")
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(service=service, options=options)
    driver.maximize_window()
    return driver


def get_room_name(room_button):
    for _ in range(4):
        room_button = room_button.find_element(By.CSS_SELECTOR, "*")
    return room_button.get_property("innerHTML")


def get_lesson_times(driver):
    timetable = wait_and_get_element(driver, TIMETABLE_XPATH).find_elements(
        By.XPATH, "./*"
    )

    # day = min(1 + datetime.today().weekday(), 5)
    days = []
    for day in range(1, 6):
        day_element = timetable[day]
        day_start_x = int(day_element.get_attribute("x"))
        day_end_x = day_start_x + int(day_element.get_attribute("width"))

        lesson_times = []

        for element in timetable:
            text = element.get_property("innerHTML").strip()

            try:
                lesson_time = str(datetime.strptime(text, "%H:%M").time())
                x = int(element.get_attribute("x"))

                if day_start_x <= x <= day_end_x:
                    lesson_times.append(lesson_time)

            except ValueError:
                pass
        days.append(list(zip(lesson_times[0::2], lesson_times[1::2])))
    return days


def get_room_indices():
    driver = initialize_driver()
    driver.get(URL)

    room_buttons = get_room_buttons(driver)

    room_indices = []

    for i, room_button in enumerate(room_buttons, 0):
        room_name = get_room_name(room_button)
        if room_name in INCLUDED_CLASSROOMS:
            room_indices.append(i)

    driver.quit()
    return room_indices


def wait_and_get_element(driver, xpath):
    while True:
        try:
            return WebDriverWait(driver, 10).until(
                ec.presence_of_element_located((By.XPATH, xpath))
            )
        except NoSuchElementException:
            time.sleep(POLL_INTERVAL)


def wait_and_click_element(driver, xpath):
    while True:
        try:
            element = WebDriverWait(driver, 10).until(
                ec.element_to_be_clickable((By.XPATH, xpath))
            )
            element.click()
            return
        except NoSuchElementException:
            time.sleep(POLL_INTERVAL)
        except ElementClickInterceptedException:
            time.sleep(POLL_INTERVAL)


def get_room_buttons(driver):
    wait_and_click_element(driver, BUTTON_XPATH)
    room_buttons = wait_and_get_element(driver, CLASSROOMS_XPATH).find_elements(
        By.XPATH, "./*"
    )
    return room_buttons


def get_room_info(button_indices):
    driver = initialize_driver()
    driver.get(URL)

    rooms = []

    for i in button_indices:
        room_buttons = get_room_buttons(driver)
        if i >= len(room_buttons):
            print(i)
            print(len(room_buttons))
        room_name = get_room_name(room_buttons[i]).strip()

        room_buttons[i].click()
        lesson_times = get_lesson_times(driver)
        driver.get(URL)
        rooms.append((room_name, lesson_times))

    driver.quit()

    return rooms


def save_lesson_times():
    if SHOULD_UPDATE_ROOM_INDICES:
        room_indices = get_room_indices()
        with open("room_indices.pickle", "wb") as file:
            pickle.dump(room_indices, file)
    else:
        with open("room_indices.pickle", "rb") as file:
            room_indices = pickle.load(file)

    pool_size = 1
    pool = Pool(pool_size)

    chunks = np.array_split(room_indices, pool_size)

    results = []

    for chunk in chunks:
        result = pool.apply_async(get_room_info, (chunk,))
        results.append(result)

    pool.close()
    pool.join()

    rooms = sum([result.get() for result in results], [])

    # with open("lesson_times.pickle", "wb") as file:
    #    pickle.dump(rooms, file)

    json_data = json.dumps(rooms)

    with open("lesson_times.json", "w") as file:
        file.write(json_data)
