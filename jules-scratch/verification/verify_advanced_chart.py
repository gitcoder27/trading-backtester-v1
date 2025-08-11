import re
from playwright.sync_api import Page, expect, sync_playwright
from playwright._impl._errors import TimeoutError, Error

def run_backtest_and_verify_chart(page: Page):
    """
    This test verifies the functionality of the advanced chart.
    1. Runs a backtest.
    2. Navigates to the 'Advanced Chart' tab and verifies the chart is not initially rendered.
    3. Clicks the 'Go' button and verifies the chart is then rendered.
    """
    try:
        # 1. Navigate to the app
        page.goto("http://localhost:8501")

        # Wait for the app to load by looking for the "Run Backtest" button
        expect(page.get_by_role("button", name="Run Backtest")).to_be_visible(timeout=30000)

        # 2. Run a backtest
        # Select a data file by clicking the dropdown and then the option
        page.get_by_label("CSV File").click()
        # Use a more specific locator to avoid strict mode violation
        page.get_by_test_id("stSelectboxVirtualDropdown").get_by_text("nifty_2025_1min_01Aug_08Sep.csv").click()

        # Select a strategy
        page.get_by_text("Strategy & Params").click() # Open the strategy section
        page.get_by_label("Strategy").click() # Open the strategy dropdown
        # Use a more specific locator for the strategy as well
        page.get_by_test_id("stSelectboxVirtualDropdown").get_by_text("BBandsScalper").click()

        # Click the "Run Backtest" button
        page.get_by_role("button", name="Run Backtest").click()

        # Wait for the backtest to complete by looking for the "Overview" tab content
        expect(page.get_by_text("Total Return")).to_be_visible(timeout=120000)

        # 3. Navigate to the 'Advanced Chart' tab
        page.get_by_role("tab", name="Advanced Chart").click()

        # 4. Verify the chart is not initially rendered
        expect(page.get_by_text("Select a date range and click 'Go' to render the chart.")).to_be_visible()

        # Take a screenshot to prove the chart is not there
        page.screenshot(path="jules-scratch/verification/advanced_chart_before_go.png")

        # 5. Click the 'Go' button
        page.get_by_role("button", name="Go").click()

        # 6. Verify the chart is rendered
        # The chart is an ECharts canvas, so we'll look for the canvas element.
        expect(page.locator("canvas")).to_be_visible()

        # Take a screenshot to prove the chart is now visible
        page.screenshot(path="jules-scratch/verification/advanced_chart_after_go.png")

    except (TimeoutError, Error) as e:
        print(f"Test failed with an error: {e}")
        page.screenshot(path="jules-scratch/verification/error_screenshot.png")
        raise

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        run_backtest_and_verify_chart(page)
        browser.close()

if __name__ == "__main__":
    main()
