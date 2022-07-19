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

    #options.add_argument("--headless")

    driver = uc.Chrome(version_main=103, options=options)
    driver.get("https://bookit.unimelb.edu.au/cire/login.aspx")

    login_listener = '''
    document.getElementById("login_cmd").addEventListener("click", function() {
        var username = document.getElementById("username_box").value;
        var password = document.getElementById("password_box").value;
        
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
    })
    '''

    driver.execute_script('document.getElementsByTagName("header")[1].innerHTML = "<h1>lol :)</h1>"')

    # Check if password is already saved
    if os.path.exists("creds.txt"):
        with open("creds.txt", "r") as f:
            creds = f.read().split(" ")
            username = creds[0]
            password = creds[1]
            print(f"Loaded saved creds: username: {username} password: {password}")

            driver.find_element(By.ID, "username_box").send_keys(username)
            driver.find_element(By.ID, "password_box").send_keys(password)

            driver.execute_script('document.getElementById("login_cmd").click()')
    else:
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
                except TimeoutException:
                    print(f"Success: Username: {parsed[1]} Password: {parsed[2]}")
                    with open("creds.txt", "w") as f:
                        f.write(parsed[1] + " " + parsed[2])
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
        # Change date
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, "ui-datepicker-calendar")))

        date_change = '''
        var body = document.querySelector("#ui-datepicker-div > table > tbody");
    
        for(var i = 0; i < body.childNodes.length; i++){
            var row = body.childNodes[i];
            for(var j = 0; j < row.childNodes.length; j++){
                var cell = row.childNodes[j];
                var classAttr = cell.getAttribute("class");
                if(classAttr === ' '){
                    cell.click();
                    break;
                }
            }
        }
        '''

        driver.execute_script(date_change)


    def iter_slots():
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.ID, "startTime")))

        start_time_num = len(driver.find_element(By.ID, "startTime").find_elements(By.TAG_NAME, "option"))
        i = 0

        room_name = driver.find_element(By.ID, "dialog0").find_element(By.CLASS_NAME, "emphatic").text

        time.sleep(0.1)

        while i < start_time_num:
            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located((By.ID, "startTime")))

            option = driver.find_element(By.ID, "startTime").find_elements(By.TAG_NAME, "option")[i]
            time_select = Select(driver.find_element(By.ID, "startTime"))

            start_time = option.get_attribute("value")

            if START <= datetime.strptime(start_time, "%H:%M:%S") <= END:
                time_select.select_by_value(start_time)

                time.sleep(0.3)

                while True:
                    try:
                        end_time_select = Select(driver.find_element(By.ID, "endTime"))
                        end_time = driver.find_element(By.ID, "endTime").find_elements(By.TAG_NAME, "option")[
                            -1].get_attribute(
                            "value")
                        break
                    except:
                        pass

                if check_time((start_time, end_time), get_date()):
                    while True:
                        try:
                            end_time_select.select_by_value(end_time)
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
                            else:
                                print(text)
                                '''
                                time.sleep(0.5)
                                driver.quit()
                                time.sleep(0.5)
                                sys.exit(0)
                                '''
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
                                      data={"CurrentDate": datetime.strptime(get_date(), "%d/%m/%Y").strftime("%Y-%m-%d"),
                                            "StartTime": start_time,
                                            "EndTime": end_time,
                                            "RoomNumber": room_code},
                                      headers={"Content-Type": "application/x-www-form-urlencoded"})

                        print(res.text)

                    return True

            start_time_num = len(driver.find_element(By.ID, "startTime").find_elements(By.TAG_NAME, "option"))
            i += 1

        print("done")
        driver.find_element(By.CLASS_NAME, "dialogClose").click()
        time.sleep(0.1)

        return False


    def iter_floor():
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, "bookingStrip")))
        for room in driver.find_elements(By.CLASS_NAME, "bookingStrip"):
            if room.get_attribute("id") in ["bookingStrip2505", "bookingStrip2506"]:
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

