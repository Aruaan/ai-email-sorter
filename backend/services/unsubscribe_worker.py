import sys
import asyncio
from playwright.async_api import async_playwright
import openai
import os
from dotenv import load_dotenv
import re
import traceback
load_dotenv()

LOGIN_KEYWORDS = ["login", "sign in", "sign-in", "log in", "authentication required"]
CAPTCHA_KEYWORDS = ["captcha", "i am not a robot", "recaptcha"]

def is_login_or_captcha(html):
    html_lower = html.lower()
    for word in LOGIN_KEYWORDS:
        if word in html_lower:
            return True, "Login page detected"
    for word in CAPTCHA_KEYWORDS:
        if word in html_lower:
            return True, "CAPTCHA detected"
    return False, None

def ai_decide_actions(html):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""
You are an automated agent that helps users unsubscribe from emails.

From the provided HTML, extract a short list of steps needed to unsubscribe.
Only include real actions based on what's visible in the HTML.

Each step should look like:
- Click the button with text "Unsubscribe"
- Click the button with id="confirm-btn"

Do not invent steps. If there's no input field or confirmation button, don't include them.

HTML:
{html}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content

async def parse_and_execute_actions(actions, page, user_email=None, log=None):
    steps = [line.strip() for line in actions.split('\n') if line.strip()]
    for step in steps:
        step_lower = step.lower()
        if "click" in step_lower and "unsubscribe" in step_lower:
            try:
                btn = page.locator("text=/unsubscribe/i")
                if await btn.count() > 0:
                    await btn.nth(0).click()
                    await page.wait_for_load_state("load")
                    if log is not None:
                        log.append("Clicked 'Unsubscribe' button.")
                else:
                    raise Exception("Unsubscribe button not found")
            except Exception as e:
                if log is not None:
                    log.append(f"Failed to click 'Unsubscribe' button: {e}")
                return False, f"Failed to click 'Unsubscribe' button: {e}"

        elif "fill" in step_lower and "input" in step_lower:
            match = re.search(r"fill input with name[=\"'](.*?)[\"'] with (.+)", step_lower)
            if match:
                input_name = match.group(1)
                value = user_email if "user email" in match.group(2) else match.group(2)
                try:
                    await page.fill(f"input[name='{input_name}']", value)
                    if log is not None:
                        log.append(f"Filled input '{input_name}' with '{value}'.")
                except Exception as e:
                    if log is not None:
                        log.append(f"Failed to fill input '{input_name}': {e}")
                    return False, f"Failed to fill input '{input_name}': {e}"

        elif "confirm" in step_lower or "submit" in step_lower:
            try:
                if "confirm" in step_lower:
                    await page.click("text=/confirm/i", timeout=3000)
                    if log is not None:
                        log.append("Clicked 'Confirm' button.")
                elif "submit" in step_lower:
                    await page.click("text=/submit/i", timeout=3000)
                    if log is not None:
                        log.append("Clicked 'Submit' button.")
            except Exception as e:
                if log is not None:
                    log.append(f"Failed to click confirm/submit: {e}")
                return False, f"Failed to click confirm/submit: {e}"
    return True, "All AI actions executed."

async def check_success(page):
    content = (await page.content()).lower()
    for word in ["unsubscribed", "success", "you have been removed", "you are now unsubscribed", "you have been unsubscribed"]:
        if word in content:
            return True, f"Success message found: '{word}'"
    return False, "No success message found after actions."

async def unsubscribe_link_worker_async(unsubscribe_url, user_email=None):
    log = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(unsubscribe_url, timeout=60000)
            html = await page.content()
            login_captcha, reason = is_login_or_captcha(html)
            if login_captcha:
                log.append(reason)
                await browser.close()
                return {
                    "success": False,
                    "reason": reason,
                    "actions": None,
                    "action_success": False,
                    "action_msg": reason,
                    "log": log
                }
            actions = ai_decide_actions(html)
            log.append(f"AI Actions: {actions}")  # Log AI response
            action_success, action_msg = await parse_and_execute_actions(actions, page, user_email, log)
            if action_success:
                success, success_msg = await check_success(page)
            else:
                success, success_msg = False, action_msg
            await browser.close()
            return {
                "success": success,
                "reason": success_msg,
                "actions": actions,
                "action_success": action_success,
                "action_msg": action_msg,
                "log": log
            }
    except Exception as e:
        tb = traceback.format_exc()
        log.append(f"Exception: {e}\n{tb}")
        return {"success": False, "reason": f"Exception: {e}", "log": log}

async def batch_unsubscribe_worker_async(unsubscribe_links, user_email=None):
    results = []
    batch_limit = 10
    for i, link in enumerate(unsubscribe_links):
        if i >= batch_limit:
            results.append({"success": False, "reason": "Batch limit exceeded (10 per call)", "link": link})
            continue
        if not link or not link.startswith("http"):
            results.append({"success": False, "reason": "Invalid link", "link": link})
            continue
        result = await unsubscribe_link_worker_async(link, user_email)
        result["link"] = link
        results.append(result)
    return results

def batch_unsubscribe_worker(unsubscribe_links, user_email=None):
    # Synchronous wrapper for FastAPI compatibility
    return asyncio.run(batch_unsubscribe_worker_async(unsubscribe_links, user_email))

if __name__ == "__main__":
    # Minimal Playwright environment test (async)
    async def main():
        print("[Playwright Test] Launching Chromium and opening example.com...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto("http://localhost:3000", timeout=15000)
                print("[Playwright Test] Page title:", await page.title())
                await browser.close()
            print("[Playwright Test] Success: Playwright is working.")
        except Exception as e:
            import traceback
            print("[Playwright Test] Exception:", e)
            print(traceback.format_exc())
    asyncio.run(main())
