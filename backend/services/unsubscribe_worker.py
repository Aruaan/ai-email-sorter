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
You are an automated agent helping a user unsubscribe from email communications.

From the provided HTML, extract a concise list of real steps needed to fully complete the unsubscribe process.

Only list actions that are visibly present in the HTML, including:
- Clicking buttons (e.g., Unsubscribe, Confirm, Continue, Next, Submit)
- Selecting radio buttons or checkboxes (e.g., reason for unsubscribing)
- Filling and submitting forms
- Clicking links

Do NOT guess. Do NOT infer actions. Only write steps if the exact elements are clearly visible in the HTML.

Format each action like this:
- Click the button with text "<actual button text>"
- Select the radio button with text "<actual label>"
- Fill input with name="<name>" with user email

If no actions are needed, respond only with:
No further action needed.

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
    executed_steps = set()
    for step in steps:
        if step in executed_steps:
            continue
        executed_steps.add(step)
        step_lower = step.lower()

        if "click" in step_lower:
            try:
                match = re.search(r'text \"(.+?)\"', step, re.IGNORECASE)
                button_text = match.group(1) if match else "unsubscribe"
                btn = page.locator(f'text=/{button_text}/i')
                if await btn.count() > 0:
                    await btn.nth(0).click()
                    await page.wait_for_timeout(2000)
                    if log is not None:
                        log.append(f"Clicked button with text '{button_text}'.")
                else:
                    raise Exception(f"Button with text '{button_text}' not found")
            except Exception as e:
                if log is not None:
                    log.append(f"Failed to click button: {e}")
                return False, f"Failed to click button: {e}"

        elif "select" in step_lower and "radio" in step_lower:
            try:
                match = re.search(r'text \"(.+?)\"', step, re.IGNORECASE)
                label_text = match.group(1) if match else None
                if label_text:
                    radio = page.locator(f'text=/{label_text}/i')
                    if await radio.count() > 0:
                        await radio.nth(0).click()
                        if log is not None:
                            log.append(f"Selected radio with label '{label_text}'.")
                    else:
                        raise Exception(f"Radio with text '{label_text}' not found")
            except Exception as e:
                if log is not None:
                    log.append(f"Failed to select radio: {e}")
                return False, f"Failed to select radio: {e}"

        elif "fill" in step_lower and "input" in step_lower:
            match = re.search(r'name[=\"\'](.*?)[\"\'].*with (.+)', step_lower)
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
    return True, "All AI actions executed."

async def check_success(page):
    content = (await page.content()).lower()
    for word in ["unsubscribed", "success", "you have been removed", "you are now unsubscribed", "you have been unsubscribed"]:
        if word in content:
            return True, f"Success message found: '{word}'"
    return False, "No success message found after actions."

# Add fallback clicker for unsubscribe elements
async def fallback_unsubscribe_click(page, log=None):
    selectors = [
        "text=/unsubscribe/i",
        "a:has-text('unsubscribe')",
        "button:has-text('unsubscribe')",
        "input[value*=unsubscribe i]",
        "[aria-label*=unsubscribe i]",
        "[title*=unsubscribe i]",
    ]
    for sel in selectors:
        try:
            el = page.locator(sel)
            if await el.count() > 0:
                await el.nth(0).click()
                if log is not None:
                    log.append(f"Fallback: Clicked element with selector '{sel}'.")
                await page.wait_for_timeout(2000)
                return True
        except Exception as e:
            if log is not None:
                log.append(f"Fallback: Failed to click '{sel}': {e}")
    return False

# Add fallback form submitter
async def fallback_submit_form(page, log=None):
    forms = await page.locator("form").all()
    if len(forms) == 1:
        try:
            await forms[0].evaluate("form => form.submit()")
            if log is not None:
                log.append("Fallback: Submitted the only form on the page.")
            await page.wait_for_timeout(2000)
            return True
        except Exception as e:
            if log is not None:
                log.append(f"Fallback: Failed to submit form: {e}")
    return False

async def unsubscribe_link_worker_async(unsubscribe_url, user_email=None):
    log = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(unsubscribe_url, timeout=60000)

            # --- BLANK PAGE CHECK ---
            html = await page.content()
            # Try to get visible text from <body>
            try:
                text = await page.inner_text('body', timeout=2000) if await page.locator('body').count() > 0 else ''
            except Exception:
                text = ''
            if not text.strip():
                await browser.close()
                log.append("Blank page detected after visiting unsubscribe link.")
                return {
                    "success": True,
                    "reason": "Blank page after visiting unsubscribe link—likely successful.",
                    "actions": None,
                    "action_success": True,
                    "action_msg": "No visible content; assumed unsubscribed.",
                    "log": log
                }
            # --- END BLANK PAGE CHECK ---

            max_steps = 5
            step_count = 0
            previous_actions = set()

            while step_count < max_steps:
                step_count += 1

                html = await page.content()
                log.append(f"HTML Snapshot (step {step_count}):\n{html[:2000]}...\n")

                login_captcha, reason = is_login_or_captcha(html)
                if login_captcha:
                    log.append(reason)
                    await page.screenshot(path=f"screenshot_login_{step_count}.png", full_page=True)
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
                log.append(f"AI Actions: {actions}")

                if actions in previous_actions:
                    log.append("Same AI actions repeated — stopping to avoid loop.")
                    break
                previous_actions.add(actions)

                if not actions or "no further action needed" in actions.lower():
                    # Try fallback clicker if AI says nothing to do
                    fallback_clicked = await fallback_unsubscribe_click(page, log)
                    if fallback_clicked:
                        await page.wait_for_timeout(2000)
                        success, success_msg = await check_success(page)
                        if success:
                            await browser.close()
                            return {
                                "success": True,
                                "reason": "Fallback unsubscribe click worked.",
                                "actions": actions,
                                "action_success": True,
                                "action_msg": "Fallback click.",
                                "log": log
                            }
                    # Try fallback form submit
                    fallback_form = await fallback_submit_form(page, log)
                    if fallback_form:
                        await page.wait_for_timeout(2000)
                        success, success_msg = await check_success(page)
                        if success:
                            await browser.close()
                            return {
                                "success": True,
                                "reason": "Fallback form submit worked.",
                                "actions": actions,
                                "action_success": True,
                                "action_msg": "Fallback form submit.",
                                "log": log
                            }
                    break

                action_success, action_msg = await parse_and_execute_actions(actions, page, user_email, log)
                if not action_success:
                    # Try fallback clicker if AI action fails
                    fallback_clicked = await fallback_unsubscribe_click(page, log)
                    if fallback_clicked:
                        await page.wait_for_timeout(2000)
                        success, success_msg = await check_success(page)
                        if success:
                            await browser.close()
                            return {
                                "success": True,
                                "reason": "Fallback unsubscribe click worked after AI action failed.",
                                "actions": actions,
                                "action_success": True,
                                "action_msg": "Fallback click after AI fail.",
                                "log": log
                            }
                    # Try fallback form submit
                    fallback_form = await fallback_submit_form(page, log)
                    if fallback_form:
                        await page.wait_for_timeout(2000)
                        success, success_msg = await check_success(page)
                        if success:
                            await browser.close()
                            return {
                                "success": True,
                                "reason": "Fallback form submit worked after AI action failed.",
                                "actions": actions,
                                "action_success": True,
                                "action_msg": "Fallback form submit after AI fail.",
                                "log": log
                            }
                    await page.screenshot(path=f"screenshot_fail_{step_count}.png", full_page=True)
                    await browser.close()
                    return {
                        "success": False,
                        "reason": action_msg,
                        "actions": actions,
                        "action_success": action_success,
                        "action_msg": action_msg,
                        "log": log
                    }

                success, success_msg = await check_success(page)
                if success:
                    await browser.close()
                    return {
                        "success": True,
                        "reason": success_msg,
                        "actions": actions,
                        "action_success": action_success,
                        "action_msg": action_msg,
                        "log": log
                    }

                # Fallback: check if unsubscribe button is gone
                button_still_there = await page.locator("text=/unsubscribe/i").count() > 0
                if button_still_there == 0:
                    log.append("Unsubscribe button no longer visible — assuming success.")
                    await browser.close()
                    return {
                        "success": True,
                        "reason": "Unsubscribe button disappeared. Likely successful.",
                        "actions": actions,
                        "action_success": True,
                        "action_msg": "All AI actions executed.",
                        "log": log
                    }

                # Try fallback clicker if nothing else worked
                fallback_clicked = await fallback_unsubscribe_click(page, log)
                if fallback_clicked:
                    await page.wait_for_timeout(2000)
                    success, success_msg = await check_success(page)
                    if success:
                        await browser.close()
                        return {
                            "success": True,
                            "reason": "Fallback unsubscribe click worked after all AI actions.",
                            "actions": actions,
                            "action_success": True,
                            "action_msg": "Fallback click after all AI actions.",
                            "log": log
                        }
                # Try fallback form submit
                fallback_form = await fallback_submit_form(page, log)
                if fallback_form:
                    await page.wait_for_timeout(2000)
                    success, success_msg = await check_success(page)
                    if success:
                        await browser.close()
                        return {
                            "success": True,
                            "reason": "Fallback form submit worked after all AI actions.",
                            "actions": actions,
                            "action_success": True,
                            "action_msg": "Fallback form submit after all AI actions.",
                            "log": log
                        }

            await page.screenshot(path=f"screenshot_timeout_{step_count}.png", full_page=True)
            await browser.close()
            return {
                "success": False,
                "reason": "No success message found after actions.",
                "actions": actions,
                "action_success": True,
                "action_msg": "All AI actions executed.",
                "log": log
            }

    except Exception as e:
        tb = traceback.format_exc()
        log.append(f"Exception: {e}\n{tb}")
        return {"success": False, "reason": f"Exception: {e}", "log": log}

async def batch_unsubscribe_worker_async(unsubscribe_links, user_email=None):
    results = []
    batch_limit = 10
    seen_links = set()
    for i, link in enumerate(unsubscribe_links):
        if i >= batch_limit:
            results.append({
                "link": link,
                "success": False,
                "reason": "Batch limit exceeded (10 per call)",
                "skipped": True
            })
            continue
        if not link or not (link.startswith("http://") or link.startswith("https://")):
            # Skip non-http(s) links (e.g., mailto:)
            results.append({
                "link": link,
                "success": False,
                "reason": "Skipped non-web unsubscribe link (e.g., mailto: or invalid)",
                "skipped": True
            })
            continue
        if link in seen_links:
            results.append({
                "link": link,
                "success": True,
                "reason": "Duplicate link, already unsubscribed in this batch",
                "duplicate": True
            })
            continue
        seen_links.add(link)
        result = await unsubscribe_link_worker_async(link, user_email)
        result["link"] = link
        results.append(result)
    return results

def batch_unsubscribe_worker(unsubscribe_links, user_email=None):
    return asyncio.run(batch_unsubscribe_worker_async(unsubscribe_links, user_email))
