from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import wait, expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from datetime import datetime

import os
import sys
import time
import platform

from time_ops import *
'''
options = Options()
options.add_argument("window-size=1400,600")

ua = UserAgent()
user_agent = ua.random
options.add_argument(f'user-agent={user_agent}')

options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(executable_path="chromedriver.exe", options=options)
'''

ROOM_NAMES= ["123", "124", "206", "207", "211", "212", "G15"]

if __name__ == "__main__":
    options = uc.ChromeOptions()

    login_listener = '''
    document.getElementById("login_cmd").addEventListener("click", function() {
        var username = document.getElementById("username_box").value;
        var password = document.getElementById("password_box").value;
        
        console.log("asdfasdfdasf");
        
        alert("value " + username + " " + password);
        
        setTimeout(function() {
            var error = document.getElementsByClassName("NewMessageBoxErrorContent")[0];
            console.log(error);
            if(error != undefined && error != null){
                alert("error " + error.innerText);
            }else{
                alert("success");
            }
        }, 500)
    });
    
    document.addEventListener("keypress", (event => {
        if (event.key == "Enter") {
            var username = document.getElementById("username_box").value;
            var password = document.getElementById("password_box").value;
            
            console.log("asdfasdfdasf");
            
            alert("value " + username + " " + password);
        }
    }));
    '''

    user = ""

    # Check if password is already saved
    if os.path.exists("creds.txt"):
        options.add_argument("--headless")
        driver = uc.Chrome(version_main=103, options=options)
        driver.get("https://bookit.unimelb.edu.au/cire/login.aspx")

        with open("creds.txt", "r") as f:
            creds = f.read().split(" ")
            username = creds[0]
            password = creds[1]
            print(f"Loaded saved creds: username: {username} password: {password}")

            driver.find_element(By.ID, "username_box").send_keys(username)
            driver.find_element(By.ID, "password_box").send_keys(password)

            driver.execute_script('document.getElementById("login_cmd").click()')
            user = username
    else:
        driver = uc.Chrome(version_main=103, options=options)
        driver.get("https://bookit.unimelb.edu.au/cire/login.aspx")

        driver.execute_script(
            'document.getElementsByTagName("header")[1].innerHTML = "<h1>Please log in to bookit :)</h1>"')
        driver.execute_script(login_listener)

        while True:
            WebDriverWait(driver, 100).until(expected_conditions.alert_is_present())
            alert = driver.switch_to.alert

            parsed = alert.text.split(" ")
            if parsed[0] == "value":
                alert.dismiss()

                try:
                    WebDriverWait(driver, 4).until(expected_conditions.alert_is_present())
                    alert = driver.switch_to.alert

                    parsed = alert.text.split(" ")
                    if parsed[0] == "error":
                        print(f"Error: {parsed[1]}")
                        alert.dismiss()
                        sys.exit(0)
                except TimeoutException:
                    print(f"Success: Username: {parsed[1]} Password: {parsed[2]}")
                    with open("creds.txt", "w") as f:
                        f.write(parsed[1] + " " + parsed[2])

                    if platform.system() == "Windows":
                        os.system("start cmd /k python main.py")
                    else:
                        print("Please re-run main.py")

                    driver.close()
                    sys.exit(0)
                    user = parsed[1]
                    break


    # 142: L1 access technology room
    # 133: L1 group space
    # 134: L2 group space
    # 146: Ground large space
    ALL_LEVELS = ["133", "134", "146"]


    def select_level(list_id):
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.ID, "locationId")))

        levels = Select(driver.find_element(By.ID, "locationId"))
        levels.select_by_value(list_id)


    def get_date():
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.ID, "gridDate")))
        date = driver.find_element(By.ID, "gridDate")
        return date.get_attribute("value")


    def select_next_workday():
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, "//a[@class='buttonIconS buttonIconS-right' and @title='Next']")))

        elem = driver.find_element(By.XPATH, "//a[@class='buttonIconS buttonIconS-right' and @title='Next']")
        elem.click()

        while datetime.strptime(get_date(), "%d/%m/%Y").weekday() > 4:
            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, "//a[@class='buttonIconS buttonIconS-right' and @title='Next']")))

            elem = driver.find_element(By.XPATH, "//a[@class='buttonIconS buttonIconS-right' and @title='Next']")

            while True:
                try:
                    elem.click()
                    break
                except:
                    pass


    def iter_slots():
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.ID, "startTime")))

        room_name = driver.find_element(By.ID, "dialog0").find_element(By.CLASS_NAME, "emphatic").text

        time.sleep(0.1)

        print(f"Looking at room {room_name} on date {get_date()}")

        free_times = populate_free(get_date())

        for time_slot in free_times:
            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located((By.ID, "startTime")))

            while True:
                try:
                    time_options = list(map(lambda x: x.get_attribute("value"),
                                       driver.find_element(By.ID, "startTime").find_elements(By.TAG_NAME, "option")))
                    break
                except:
                    pass

            prev_end_time = None
            for start_time in time_options:
                start_time_dt = datetime.strptime(start_time, "%H:%M:%S")

                if start_time_dt >= time_slot[1]:
                    break

                if prev_end_time is not None and start_time_dt < datetime.strptime(prev_end_time, "%H:%M:%S"):
                    continue

                if start_time_dt >= time_slot[0] and START <= start_time_dt <= END:
                    Select(driver.find_element(By.ID, "startTime")).select_by_value(start_time)
                    time.sleep(0.3)

                    while True:
                        try:
                            end_time_options = list(map(lambda x: x.get_attribute("value"),
                                       driver.find_element(By.ID, "endTime").find_elements(By.TAG_NAME, "option")))
                            break
                        except:
                            pass

                    for end_time in reversed(end_time_options):
                        prev_end_time = end_time
                        if check_time((start_time, end_time), get_date()):
                            while True:
                                try:
                                    Select(driver.find_element(By.ID, "endTime")).select_by_value(end_time)
                                    driver.find_element(By.ID, "submitButton").click()
                                    break
                                except:
                                    pass

                            time.sleep(1)

                            try:
                                text = driver.find_element(By.CLASS_NAME, "expectedException").text
                                if text != "":
                                    if text == "Bookings are limited to one hour per day per site.":
                                        print("Site booking exceeded")
                                        driver.find_element(By.CLASS_NAME, "dialogClose").click()

                                        return "break"
                                    elif text == "Maximum outstanding bookings time limit reached!":
                                        print("Maximum booking exceeded.")
                                        # cleanup
                                        driver.close()
                                        driver.quit()
                                        time.sleep(0.5)
                                        sys.exit(0)
                                    else:
                                        print(text)
                                        while True:
                                            pass
                            except NoSuchElementException as e:
                                print(f"Found a slot for {room_name} at {start_time} - {end_time}")
                                insert_reserved_time((start_time, end_time), get_date())

                                room_code = None
                                for code in ROOM_NAMES:
                                    if code in room_name:
                                        room_code = code

                                res = requests.post(url="http://mangotests.asuscomm.com/recordnewbooking",
                                                    data={"CurrentDate": datetime.strptime(get_date(),
                                                                                           "%d/%m/%Y").strftime(
                                                        "%Y-%m-%d"),
                                                        "StartTime": start_time,
                                                        "EndTime": end_time,
                                                        "RoomNumber": room_code,
                                                        "BookedBy": user},
                                                    headers={"Content-Type": "application/x-www-form-urlencoded"})

                                print(res.text)

                            return True

        driver.find_element(By.CLASS_NAME, "dialogClose").click()
        time.sleep(0.1)

        return False


    def iter_floor():
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, "bookingStrip")))
        for room in driver.find_elements(By.CLASS_NAME, "bookingStrip"):
            while True:
                try:
                    room_id = room.get_attribute("id")
                    break
                except:
                    pass

            if room_id in ["bookingStrip2505", "bookingStrip2506"]:
                continue

            for slots in room.find_elements(By.TAG_NAME, "div"):
                while True:
                    try:
                        slot_select = slots.get_attribute("class")
                        break
                    except:
                        pass

                if slot_select == "ts tsWht":
                    while True:
                        try:
                            slots.click()
                            break
                        except:
                            pass

                    res = iter_slots()
                    if res == "break":
                        return
                    else:
                        break


    # Wait until page is loaded (select list is loaded)
    WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.ID, "siteId")))

    # Select ERC
    loc_list = Select(driver.find_element(By.ID, "siteId"))
    loc_list.select_by_value("22")

    select_next_workday()

    while True:
        for floor in ALL_LEVELS:
            select_level(floor)
            time.sleep(1)
            iter_floor()

        select_next_workday()

