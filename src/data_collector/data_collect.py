from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import argparse
import json
import time
import re

config_path = Path(__file__).resolve().parents[2] / "config" / "collector_config.json"

with config_path.open(encoding="utf-8") as config_file:
    config = json.load(config_file)

# ==================== CONFIGURATION ====================
URL = config.get("url")
OUTPUT_FILE = config.get("output", "output/toto_results.csv")
TARGET_DATE_STR = config.get("date")
# =======================================================

def parse_date(date_str):
    """Parses various Singapore Pools date formats into a standard datetime object."""
    if not date_str:
        return None
    cleaned = re.sub(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s*', '', date_str.strip())
    for fmt in ("%d %b %Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


def get_available_dates(page):
    """Extracts unique draw items containing both their backend values and visible date texts."""
    page.wait_for_selector("select option", timeout=12000, state="attached")
    
    # CHANGE: Extract objects matching both the raw value and visible text layout
    raw_items = page.evaluate("""() => {
        const options = Array.from(document.querySelectorAll('select option'));
        return options.map(opt => ({
            value: opt.value || opt.textContent.trim(),
            text: opt.textContent.trim()
        })).filter(item => item.text);
    }""")
    
    # De-duplicate while maintaining chronological listing order
    seen = set()
    unique_items = []
    for item in raw_items:
        if item['value'] not in seen:
            seen.add(item['value'])
            unique_items.append(item)
            
    return unique_items


def select_dropdown_date(page, target_value):
    """Selects the draw option and handles full-page navigation reloads safely."""
    dropdown_selector = "select"
    page.wait_for_selector(dropdown_selector, timeout=8000)
    
    # Check if the target option is already the currently selected value in the browser DOM
    is_already_selected = page.evaluate(f"""(val) => {{
        const sel = document.querySelector('select');
        return sel ? (sel.value === val) : false;
    }}""", str(target_value))
    
    if is_already_selected:
        return

    # FIX: Wrap the dropdown change and event dispatch in an explicit wait_for_navigation context.
    # This prevents Playwright from running lines on a dead execution snapshot frame.
    try:
        with page.expect_navigation(timeout=10000, wait_until="domcontentloaded"):
            page.select_option(dropdown_selector, value=str(target_value))
            page.evaluate("""() => {
                const sel = document.querySelector('select');
                if (sel) {
                    sel.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }""")
    except Exception:
        # Fallback if the script fires changing options but the browser updates components inline instead
        pass

    # Ensure the newly loaded destination frame grid settles completely
    page.wait_for_selector("td.win1", timeout=8000)
    time.sleep(0.4)


def extract_additional_number(table, soup):
    """Finds the isolated additional lottery number using classes or text context tags."""
    additional_el = (
        table.select_one("td.additional") or 
        table.select_one("td.additional-number") or
        table.find_next("td", class_="additional")
    )
    
    if additional_el and additional_el.text.strip().isdigit():
        return additional_el.text.strip()
        
    # Text-matching fallback inside the entire content container
    for cell in soup.find_all(["td", "div", "span"]):
        if "additional" in cell.text.lower():
            nums = [s for s in re.findall(r'\b\d{1,2}\b', cell.text) if 1 <= int(s) <= 49]
            if nums:
                return nums[0]
    return "null"


def parse_draw_table(html_content, default_date_str):
    """Parses a fully rendered table block into a clean, formatted CSV row string."""
    soup = BeautifulSoup(html_content, "html.parser")
    
    table = None
    for selector in ["table.table-draw-list", ".tables-wrapper table", "table.toto-table", "table"]:
        candidate = soup.select_one(selector)
        if candidate and candidate.select_one("td.win1"):
            table = candidate
            break
            
    if not table:
        cell_check = soup.select_one("td.win1")
        if cell_check:
            table = cell_check.find_parent("table")

    if not table:
        return None

    date_obj = parse_date(default_date_str)
    if not date_obj:
        return None
    formatted_date = date_obj.strftime("%Y-%m-%d")

    winning_numbers = []
    for i in range(1, 7):
        num_cell = table.select_one(f"td.win{i}")
        if num_cell and num_cell.text.strip().isdigit():
            winning_numbers.append(num_cell.text.strip())

    if len(winning_numbers) != 6:
        return None

    additional_num = extract_additional_number(table, soup)
    return f"{formatted_date},{','.join(winning_numbers)},{additional_num}"


def save_to_csv(data_rows, filename=OUTPUT_FILE, append=False):
    """Writes the gathered lottery rows into a structured CSV file with proper headers."""
    if not data_rows:
        print("\nNo data collected to save.")
        return

    try:
        if append:
            existing_rows = []
            existing_rows_set = set()
            file_path = Path(filename)

            if file_path.exists():
                with open(filename, mode="r", encoding="utf-8") as file:
                    existing_rows = [line.strip() for line in file if line.strip()]
                    existing_rows_set = set(existing_rows)

            new_rows = [row for row in data_rows if row not in existing_rows_set]
            if not new_rows:
                print(f"\nNo new rows to append to '{filename}'")
                return

            # Put new unique rows at the top, then keep existing rows below.
            with open(filename, mode="w", encoding="utf-8") as file:
                for row in new_rows:
                    file.write(f"{row}\n")
                for row in existing_rows:
                    file.write(f"{row}\n")

            print(f"\nSuccessfully prepended {len(new_rows)} new rows to '{filename}'")
            return

        with open(filename, mode="w", encoding="utf-8") as file:
            # Write each generated combination line row by row
            for row in data_rows:
                file.write(f"{row}\n")

        print(f"\nSuccessfully saved {len(data_rows)} rows to '{filename}'")
    except IOError as e:
        print(f"Error saving data to CSV file: {e}")


def main(append=False):
    limit_date = parse_date(TARGET_DATE_STR)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Navigating to Singapore Pools...", flush=True)
        page.goto(URL, wait_until="domcontentloaded")
        
        try:
            page.wait_for_selector("td.win1", timeout=12000)
        except Exception:
            print("Error: The primary lottery data table cells failed to render in time.")
            browser.close()
            return
        
        try:
            available_draws = get_available_dates(page)
        except Exception as e:
            print(f"Extraction halted: {e}")
            browser.close()
            return

        print("\n--- STARTING DATA EXTRACTION ---", flush=True)
        collected_rows = []
        
        for draw_item in available_draws:
            current_date_obj = parse_date(draw_item['text'])

            if limit_date and current_date_obj and current_date_obj < limit_date:
                print(f"Reached boundary date ({draw_item['text']}). Stopping collection loop.")
                break

            try:
                select_dropdown_date(page, draw_item['value'])
                csv_line = parse_draw_table(page.content(), default_date_str=draw_item['text'])
                if csv_line:
                    print(csv_line, flush=True)
                    collected_rows.append(csv_line)
            except Exception:
                # Silently drop single entry errors to keep driving down the time-series loop array
                continue
                
        browser.close()

    save_to_csv(collected_rows, append=append)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--append",
        action="store_true",
        help="Prepend only new rows to the top of the output file.",
    )
    args = parser.parse_args()
    main(append=args.append)