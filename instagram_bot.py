import os
import time
import pickle
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pyperclip

COOKIES_FILE = "cookies/insta_session.pkl"
INSTAGRAM_URL = "https://www.instagram.com"

class InstagramBot:
    def __init__(self, headless=False):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        if headless:
            chrome_options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.implicitly_wait(5)
        self.logged_in = False

    def login(self, wait_callback=None):
        os.makedirs("cookies", exist_ok=True)

        self.driver.get(f"{INSTAGRAM_URL}/accounts/login/")
        time.sleep(3)

        if os.path.exists(COOKIES_FILE):
            self._load_cookies()
            self.driver.get(INSTAGRAM_URL)
            time.sleep(3)
            if self._check_logged_in():
                print("✅ Session restored.")
                self.logged_in = True
                return True

        print("🔐 Please log in manually...")

        if wait_callback:
            wait_callback()

        if self._check_logged_in():
            self._save_cookies()
            self.logged_in = True
            print("✅ Login successful. Session saved.")
            return True
        else:
            print("❌ Login failed.")
            return False

    def logout(self):
        if os.path.exists(COOKIES_FILE):
            os.remove(COOKIES_FILE)
            print("🧹 Session cookies cleared.")
        self.driver.get(f"{INSTAGRAM_URL}/accounts/logout/")
        time.sleep(3)

    def is_logged_in(self):
        return self.logged_in

    def send_dm_to(self, username, message, mode="manual"):
        try:
            self.driver.get(f"{INSTAGRAM_URL}/{username}/")
            time.sleep(3)

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            try:
                message_button = self.driver.find_element(By.XPATH, "//div[text()='Message']")
                message_button.click()
            except NoSuchElementException:
                try:
                    print("⚠️ Trying alternate message button for private account")
                    menu_btn = self.driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[2]/div/div/div[3]")
                    menu_btn.click()
                    time.sleep(2)
                    message_button_2 = self.driver.find_element(By.XPATH, "/html/body/div[4]/div[1]/div/div[2]/div/div/div/div/div/button[6]")
                    message_button_2.click()
                except Exception as e:
                    print(f"❌ Message button not found for {username}: {e}")
                    return False

            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='textbox' and @contenteditable='true']"))
            )

            textarea = self.driver.find_element(By.XPATH, "//div[@role='textbox' and @contenteditable='true']")
            self.driver.execute_script("arguments[0].focus();", textarea)
            time.sleep(1)

            # ✅ Emoji-safe paste using clipboard
            pyperclip.copy(message)
            actions = ActionChains(self.driver)
            actions.move_to_element(textarea).click().key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()
            time.sleep(1)

            if mode == "auto":
                textarea.send_keys(Keys.ENTER)
                print(f"✅ DM sent to: {username}")
            else:
                print(f"🕒 Manual review required for @{username}. Click Send manually if needed.")

            try:
                popup = self.driver.find_element(By.XPATH, "//div[@role='dialog']")
                print(f"⚠️ Popup detected for {username}, please check manually.")
            except NoSuchElementException:
                pass

            return True

        except Exception as e:
            print(f"❌ Error sending DM to {username}: {e}")
            return False

    def close(self):
        self.driver.quit()

    def _check_logged_in(self):
        try:
            self.driver.find_element(By.XPATH, "//a[contains(@href, '/direct/inbox')] | //span[@aria-label='Profile']")
            return True
        except NoSuchElementException:
            return False

    def _save_cookies(self):
        with open(COOKIES_FILE, "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)

    def _load_cookies(self):
        self.driver.get(INSTAGRAM_URL)
        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                print(f"⚠️ Failed to set cookie: {e}")