import sys
import time
import random
import config
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.proxy import Proxy, ProxyType
import requests


def driver_init(proxy=None):
    print('Driver initialization...')
    try:
        if config.drv=='Firefox':
            options = webdriver.firefox.options.Options()
            if config.headless=='True':
                options.headless = True
            else:
                options.headless = False
            profile = webdriver.FirefoxProfile()
            profile.set_preference("browser.download.folderList", 2)
            profile.set_preference("browser.download.manager.alertOnEXEOpen", False)
            profile.set_preference("browser.helperApps.neverAsk.saveToDisk",
                                   """application/msword, application/csv, application/ris,
                                  text/csv, image/png, application/pdf, text/html, text/plain,
                                  application/zip, application/x-zip, application/x-zip-compressed,
                                  application/download, application/octet-stream""")
            profile.set_preference("browser.download.manager.showWhenStarting", False)
            profile.set_preference("browser.download.manager.focusWhenStarting", False);
            profile.set_preference("browser.download.useDownloadDir", True)
            profile.set_preference("browser.helperApps.alwaysAsk.force", False)
            profile.set_preference("browser.download.manager.alertOnEXEOpen",False)
            profile.set_preference("browser.download.manager.closeWhenDone", True)
            profile.set_preference("browser.download.manager.showAlertOnComplete", False)
            profile.set_preference("browser.download.manager.useWindow", False)
            profile.set_preference("services.sync.prefs.sync.browser.download.manager.showWhenStarting", False)
            profile.set_preference("pdfjs.disabled", True)
            profile.set_preference("general.useragent.override", config.user_agent)
            if config.disable_images=='True':
                profile.set_preference("permissions.default.image", 2)
            driver = webdriver.Firefox(firefox_profile=profile, options=options)
            print('Geckodriver load... success')
            return driver
        elif config.drv=='Chrome':
            options = webdriver.ChromeOptions()
            if config.headless=='True':
                options.add_argument('headless')
                options.add_argument('no-sandbox')
                options.add_argument('disable-dev-shm-usage')
            if config.disable_images=='True':
                prefs = {"profile.managed_default_content_settings.images": 2}
                options.add_experimental_option("prefs", prefs)
            options.add_argument('user-agent=%s'%(config.user_agent))
            options.add_argument('disable-gpu')
            options.add_argument('log-level=3')
            options.add_argument("ignore-certificate-errors")
            if proxy!=None:
                options.add_argument('--proxy-server=socks5://%s' % proxy)
            capabilities = options.to_capabilities()
            driver = webdriver.Chrome(desired_capabilities=capabilities)
            driver.set_window_size(1024,768)
            print('Chromedriver load... success')
            return driver
        elif config.drv=='PhantomJS':
            capabilities = webdriver.DesiredCapabilities.PHANTOMJS
            if config.disable_images=='True':
                capabilities["phantomjs.page.settings.loadImages"] = True
            capabilities["phantomjs.page.settings.userAgent"] = config.user_agent
            driver = webdriver.PhantomJS(desired_capabilities=capabilities, service_args=['--ignore-ssl-errors=true', '--ssl-protocol=TLSv1'])
            driver.set_window_size(1024,768)
            print('PhantomJS load... success')
            return driver
        elif config.drv=='Opera':
            print("Opera load")
            config.options = webdriver.ChromeOptions()
            if config.headless=='True':
                options.add_argument('headless')
            if config.disable_images=='True':
                prefs = {"profile.managed_default_content_settings.images": 2}
                options.add_experimental_option("prefs", prefs)
            options.add_argument('user-agent=%s'%(config.user_agent))
            options.add_argument('disable-gpu')
            options.add_argument('log-level=3')
            options.add_argument("ignore-certificate-errors")
            if proxy!=None:
                options.add_argument('--proxy-server=socks5://%s' % proxy)
            capabilities = options.to_capabilities()
            driver = webdriver.Opera(desired_capabilities=capabilities)
            print('Opera load... success')
            return driver
    except :
        print("Can't load driver")
        print (sys.exc_info())


def driver_close(driver):
     driver.get("about:blank")
     driver.close()
     print('Close driver... success')

def open_site(driver,site,xpath):
    print('Open ',site)
    error=0
    driver.implicitly_wait = config.implicitly_wait
    while True:
        start_time = time.time()
        driver.get(site)
        try:
            WebDriverWait(driver, config.driver_delay).until(EC.presence_of_element_located((By.XPATH ,xpath)))
            time.sleep(random.randint(3, 5))
            print ("Page is ready!","%s seconds" % (time.time() - start_time))
            return True
        except TimeoutException:
            error=error+1
            print ("Loading took too much time!-Try again","%s seconds" % (time.time() - start_time))
            if error > config.max_repeat:
                print('Error open site... ', site)
                return False

def scrollDown(driver, value):
    driver.execute_script("window.scrollBy(0,"+str(value)+")")

def scrollDownAllTheWay(driver):
    old_page = driver.page_source
    while True:
        for i in range(2):
            scrollDown(driver, 2000)
            time.sleep(3)
        new_page = driver.page_source
        if new_page != old_page:
            old_page = new_page
        else:
            break
    return True

def scrollDowntoXpath(driver,xpath):
    old_page = driver.page_source
    while (not driver.find_element(By.XPATH, xpath)):
        for i in range(2):
            scrollDown(driver, 2000)
            time.sleep(3)
        new_page = driver.page_source
        if new_page != old_page:
            old_page = new_page
        else:
            return False
    return True

def get_request(link, params={}):
    time.sleep(random.randint(1, 3))
    try:
        while True:
            response = requests.get(link, headers={'User-Agent':config.user_agent}, params=params)
            break
    except:
        print("Error connect... ", link)
        print (sys.exc_info())
        return None
    if response.status_code != 200:
        print('Server returned status code %s' % response.status_code)
        return None
    else:
        return response.content

def click_button(driver, xpath_button):
    try:
        btn = driver.find_element(By.XPATH, xpath_button)
        ActionChains(driver).move_to_element(btn).click().perform()
        time.sleep(random.randint(3, 5))
        print('Click button ...',xpath_button,' Success')
        return True

    except:
        print('Click button ...',xpath_button,' False')
        return False

def click_element(driver, element):
    try:
        ActionChains(driver).move_to_element(element).click().perform()
        time.sleep(random.randint(3, 5))
        print('Click element ...',element,' Success')
        return True

    except:
        print('Click element ...',element,' False')
        return False

def find_elements(driver, element):
    try:
        elements = driver.find_elements(By.XPATH, element)
        return elements

    except:
        print (sys.exc_info())
        print('No elements find ... ',element)
        return None


def wait_to_element(driver,xpath):
    print('Wait element... ',xpath)
    error=0
    driver.implicitly_wait = config.implicitly_wait
    while True:
        start_time = time.time()
        try:
            WebDriverWait(driver, config.driver_delay).until(EC.presence_of_element_located((By.XPATH ,xpath)))
            print ("Element find...","%s seconds" % (time.time() - start_time))
            return True
        except TimeoutException:
            error=error+1
            print ("Element not find...-Try again","%s seconds" % (time.time() - start_time))
            if error>config.max_repeat:
                print('Error find element... ', xpath)
                return False
