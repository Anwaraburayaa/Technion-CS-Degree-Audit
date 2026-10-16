from playwright.sync_api import sync_playwright  # library that controls a real browser from Python

APP_URL = "https://technion-cs-degree-audit-8zz3utn44pyn3xjpnshfqd.streamlit.app/"  # your app's link

with sync_playwright() as p:  # start Playwright and close it automatically at the end
    browser = p.chromium.launch(headless=True)  # open Chromium with no visible window
    page = browser.new_page()  # open a new tab
    page.goto(APP_URL, timeout=60000)  # go to the app, wait up to 60 seconds
    page.wait_for_timeout(5000)  # wait 5 seconds so the page finishes loading
    button = page.get_by_role("button", name="Yes, get this app back up!")  # find the wake-up button
    if button.count() > 0:  # if the button exists, the app is asleep
        button.click()  # click it to wake the app
        print("App was asleep, clicked wake-up button")  # log it in the GitHub Actions output
        page.wait_for_timeout(60000)  # give the app 60 seconds to boot
    else:  # no button means the app is already awake
        print("App is already awake")  # log that nothing was needed
    browser.close()  # close the browser
