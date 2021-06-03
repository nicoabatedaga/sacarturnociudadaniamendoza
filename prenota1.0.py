from logging import exception
import os
import signal
import time
import pytz

import telegram
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from telegram import message
from telegram.ext import Filters, MessageHandler, Updater

load_dotenv()

SEDE = os.getenv("SEDE")
USUARIO = os.getenv("USUARIO")
PASSWORD = os.getenv("PASSWORD")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_BOT_CHANNEL = os.getenv("TELEGRAM_BOT_CHANNEL")

DIRECCION = os.getenv("DIRECCION")
CANT_HIJOS = os.getenv("CANT_HIJOS")
CELULAR = os.getenv("CELULAR")
LOCALIDAD = os.getenv("LOCALIDAD")
CODIGO_POSTAL = os.getenv("CODIGO_POSTAL")

CAPTCHA_FILE_NAME = "captcha.png"

bot = telegram.Bot(TELEGRAM_BOT_TOKEN)

options = Options()
#options.headless = True
driver = webdriver.Chrome("/Users/nabatedaga/personalproyectos/WebDriver/chromedriver", options=options, service_log_path="chromedriver.log")

def to_main_page():
    driver.get(f"https://prenotaonline.esteri.it/Login.aspx?ReturnUrl=%2Fdefault.aspx&cidsede={SEDE}")
    return WebDriverWait(driver, 10)

def navegate_to_login():
    # Log-in
    driver.find_element_by_name("BtnLogin").click()

def do_login(wait, chargeUser, chargePass):
    if chargeUser == True:
        driver.find_element_by_name("UserName").send_keys(USUARIO)
    if chargePass == True:
        driver.find_element_by_name("Password").send_keys(PASSWORD)
    # Mando el captcha a telegram y espero la respuesta
    # Termino con el captcha cargado
    message_listener(wait)
    # Apreto login
    driver.find_element_by_css_selector("input[value='Login']").click()
    try:
        driver.find_element_by_id("FailureText")
        return False
    except NoSuchElementException:
        return True

def fill_captcha(update, context):
    user_input = update.message.text
    captcha_input = driver.find_element_by_css_selector("input[title*='Codigo de verificación']")
    captcha_input.send_keys(user_input)
    os.kill(os.getpid(), signal.SIGINT)

def message_listener(wait):
    captcha_img = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "img[src*='captcha']")))
    captcha_img.screenshot(CAPTCHA_FILE_NAME)
    bot.send_photo(photo=open(CAPTCHA_FILE_NAME, "rb"), chat_id=TELEGRAM_BOT_CHANNEL)
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text, fill_captcha))
    updater.start_polling(poll_interval=0, timeout=30000000)
    updater.idle(signal.SIGINT)

def go_to_form(wait):
    time.sleep(1)  # wait below is not working
    solicite_un_turno = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_repFunzioni_ctl00_btnMenuItem")))
    solicite_un_turno.click()
    time.sleep(1)  # wait below is not working
    ciudadania = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_rpServizi_ctl01_btnNomeServizio")))
    ciudadania.click()

def fill_form():
    driver.find_element_by_id("ctl00_ContentPlaceHolder1_acc_datiAddizionali1_mycontrol1").send_keys(LOCALIDAD)
    driver.find_element_by_id("ctl00_ContentPlaceHolder1_acc_datiAddizionali1_mycontrol2").send_keys(CELULAR)
    driver.find_element_by_id("ctl00_ContentPlaceHolder1_acc_datiAddizionali1_mycontrol3").send_keys(DIRECCION)
    driver.find_element_by_id("ctl00_ContentPlaceHolder1_acc_datiAddizionali1_mycontrol4").send_keys(CANT_HIJOS)
    driver.find_element_by_id("ctl00_ContentPlaceHolder1_acc_datiAddizionali1_btnContinua").click()

def check_if_logout():
    try:
        driver.find_element_by_id("LblNosede")
        return True
    except NoSuchElementException:
        return False

def check_and_refresh_free_days_on_calendar():
    libres = []
    while not libres:
        driver.refresh()
        if check_if_logout():
            return False
        libres = driver.find_elements_by_css_selector(".calendarCellOpen input")
        if not libres:
            libres = driver.find_elements_by_css_selector(".calendarCellMed input")
    try:
        bot.send_message(text="Jujuu hay turnos libres", chat_id=TELEGRAM_BOT_CHANNEL)
    except:
        bot.send_message(text="Cagamos, algo se rompio: "+exception, chat_id=TELEGRAM_BOT_CHANNEL)
        print(exception)
        pass
    libres[-1].click()
    return True

def begin_process():
    wait = to_main_page()
    navegate_to_login()
    login = do_login(wait, True, True)
    while not login:
        bot.send_message(text="Pone bien el captcha rey", chat_id=TELEGRAM_BOT_CHANNEL)
        login = do_login(wait, False, True)
    bot.send_message(text="Logueado perro", chat_id=TELEGRAM_BOT_CHANNEL)
    go_to_form(wait)
    fill_form()
    done = check_and_refresh_free_days_on_calendar()
    if done == False:
        #Vuelvo a empezar
        bot.send_message(text="Nos patearon pa... logueate de nuevo...", chat_id=TELEGRAM_BOT_CHANNEL)
        begin_process()
    driver.find_element_by_id("ctl00_ContentPlaceHolder1_acc_Calendario1_repFasce_ctl01_btnConferma").click()
    message_listener(wait)  # 2nd captcha
    driver.find_element_by_id("ctl00_ContentPlaceHolder1_captchaConf").click()
    driver.save_screenshot('screenshot.png')


if __name__ == "__main__":
    # now = datetime.now().astimezone()
    # while 
    bot.send_message(text="-----------------------\nEmpezando para: "+USUARIO, chat_id=TELEGRAM_BOT_CHANNEL)
    begin_process()
