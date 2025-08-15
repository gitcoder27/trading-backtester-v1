from playwright.sync_api import sync_playwright, expect

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.set_default_timeout(60000)

            page.goto("http://localhost:8501")

            expect(page.get_by_text("Strategy Backtester")).to_be_visible()

            # Use a more robust way to select the strategy
            page.get_by_label("Strategy", exact=True).click()
            page.get_by_text("RSICrossStrategy").click()

            run_button = page.get_by_role("button", name="Run Backtest")
            expect(run_button).to_be_enabled()
            run_button.click()

            advanced_chart_tab = page.get_by_text("Advanced Chart", exact=True)
            expect(advanced_chart_tab).to_be_visible()
            advanced_chart_tab.click()

            # Wait for the chart to be rendered
            expect(page.locator("canvas").nth(1)).to_be_visible()

            page.wait_for_timeout(2000)

            screenshot_path = "jules-scratch/verification/advanced_chart.png"
            page.screenshot(path=screenshot_path)

            print(f"Screenshot saved to {screenshot_path}")

        except Exception as e:
            print(f"An error occurred: {e}")
            error_path = "jules-scratch/verification/error_screenshot.png"
            page.screenshot(path=error_path)
            print(f"Error screenshot saved to {error_path}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_verification()
