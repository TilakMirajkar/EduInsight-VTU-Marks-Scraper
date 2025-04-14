import time
import pandas as pd
import pytesseract
from io import BytesIO
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from PIL import Image
from django.http import HttpResponse, JsonResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

class ResultScraperService:
    def execute_scraping(
        self, prefix_usn: str, usn_range: str, url: str, is_reval: bool
    ) -> HttpResponse:
        """Main method to execute the complete scraping workflow"""
        try:
            usn_list = self._generate_usn_list(prefix_usn, usn_range)
            driver = self._initialize_webdriver(url)
            try:
                soup_dict = self._scrape_data(driver, usn_list)
                if not soup_dict:
                    print("No data scraped for any USN.")
                    return JsonResponse({"error": "No data found for provided USNs"}, status=404)
                df = self._process_data(soup_dict, is_reval)
                if df is None or df.empty:
                    print("Processed data is empty.")
                    return JsonResponse({"error": "No valid data processed"}, status=404)
                return self.create_excel_response(df)
            finally:
                driver.quit()
        except Exception as e:
            print(f"Scraping failed: {str(e)}")
            return JsonResponse({"error": f"Scraping failed: {str(e)}"}, status=500)

    def _generate_usn_list(self, prefix_usn: str, suffix_usn: str) -> List[str]:
        """Generate list of USNs based on prefix and range"""
        usn_list = []
        try:
            for part in suffix_usn.split(','):
                if '-' in part:
                    try:
                        start, end = map(int, part.split('-'))
                        usn_list.extend(f"{prefix_usn}{str(num).zfill(3)}" for num in range(start, end + 1))
                    except ValueError:
                        print(f"Invalid range: {part}")
                else:
                    try:
                        num = int(part)
                        usn_list.append(f"{prefix_usn}{str(num).zfill(3)}")
                    except ValueError:
                        print(f"Invalid USN suffix: {part}")
            return usn_list
        except Exception as e:
            print(f"Error generating USN list: {str(e)}")
            return []

    def _initialize_webdriver(self, url: str) -> webdriver.Chrome:
        """Initialize and return a configured webdriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=webdriver.chrome.service.Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        print(f"Navigated to {url}")
        return driver

    def _scrape_data(self, driver: webdriver.Chrome, usn_list: List[str]) -> Dict[str, BeautifulSoup]:
        """Scrape data for each USN in the list"""
        soup_dict = {}
        for usn in usn_list:
            retries = 0
            max_retries = 3
            while retries < max_retries:
                try:
                    # Clear and enter USN
                    usn_field = driver.find_element(By.NAME, 'lns')
                    usn_field.clear()
                    usn_field.send_keys(usn)

                    # Handle captcha
                    captcha_image = driver.find_element(By.XPATH, '//*[@id="raj"]/div[2]/div[2]/img').screenshot_as_png
                    captcha_text = self._get_captcha_from_image(captcha_image)

                    # Enter captcha and submit
                    captcha_field = driver.find_element(By.NAME, 'captchacode')
                    captcha_field.clear()
                    captcha_field.send_keys(captcha_text)
                    driver.find_element(By.ID, 'submit').click()

                    # Handle alert if present
                    try:
                        WebDriverWait(driver, 1).until(EC.alert_is_present())
                        alert = driver.switch_to.alert
                        alert_text = alert.text
                        alert.accept()
                        if 'University Seat Number is not available or Invalid..!' in alert_text:
                            print(f"USN {usn} not found. Skipping...")
                            break
                        print(f"Captcha failed for USN {usn}, retrying...")
                        retries += 1
                        continue
                    except:
                        # No alert means success
                        print(f"Successfully retrieved data for USN {usn}")
                        soup = BeautifulSoup(driver.page_source, 'lxml')
                        student_usn = soup.find_all('td')[1].text.split(':')[1].strip().upper()
                        student_name = soup.find_all('td')[3].text.split(':')[1].strip()
                        key = f'{student_usn}+{student_name}'
                        soup_dict[key] = soup
                        driver.back()
                        break

                except Exception as e:
                    print(f"Error processing USN {usn}: {str(e)}")
                    retries += 1
                    if retries == max_retries:
                        print(f"Max retries reached for USN {usn}. Skipping...")
                        break
                time.sleep(1)
        return soup_dict

    def _get_captcha_from_image(self, target_image: bytes) -> str:
        """Extract text from captcha image"""
        try:
            pixel_range = [(i, i, i) for i in range(102, 130)]
            image_data = BytesIO(target_image)
            image = Image.open(image_data).convert("RGB")
            width, height = image.size
            white_image = Image.new("RGB", (width, height), "white")

            # Filter pixels
            for x in range(width):
                for y in range(height):
                    pixel = image.getpixel((x, y))
                    if pixel in pixel_range:
                        white_image.putpixel((x, y), pixel)

            # Extract text using OCR
            text = pytesseract.image_to_string(white_image, config='--psm 7 --oem 1').strip()
            if len(text) < 6:
                text = text.ljust(6, 'A')
            elif len(text) > 6:
                text = text[:6]
            print(f"Captcha text extracted: {text}")
            return text
        except Exception as e:
            print(f"Tesseract OCR failed: {str(e)}")
            return "AAAAAA"  # Fallback

    def _process_data(self, soup_dict: Dict[str, BeautifulSoup], is_reval: bool) -> Optional[pd.DataFrame]:
        """Process the scraped data into a structured DataFrame"""
        records = {}
        subject_codes = []

        for id_, soup in soup_dict.items():
            this_usn, this_name = id_.split('+')
            sems_divs = soup.find_all('div', style="text-align:center;padding:5px;")
            if not sems_divs:
                print(f"No semester data for USN {this_usn}")
                continue

            first_sem_div = sems_divs[0]
            sems_data = [first_sem_div.find_next_sibling('div')]
            student_record = {'USN': this_usn, 'Student Name': this_name}

            for marks_data in sems_data:
                if not marks_data:
                    print(f"No marks data for USN {this_usn}")
                    continue
                rows = marks_data.find_all('div', class_='divTableRow')
                if not rows:
                    print(f"No table rows for USN {this_usn}")
                    continue
                data = [[cell.text.strip() for cell in row.find_all('div', class_='divTableCell')] for row in rows]
                if not data or len(data) < 2:
                    print(f"Invalid table data for USN {this_usn}: {data}")
                    continue
                try:
                    df_temp = pd.DataFrame(data[1:], columns=data[0])
                except Exception as e:
                    print(f"Failed to create DataFrame for USN {this_usn}: {str(e)}")
                    continue

                for _, row in df_temp.iterrows():
                    if 'Subject Code' not in row or 'Total' not in row:
                        print(f"Missing Subject Code or Total for USN {this_usn}")
                        continue
                    subject_code = row['Subject Code']
                    total_marks = row['Total']
                    if not isinstance(total_marks, str) or not total_marks.isdigit():
                        print(f"Invalid marks for USN {this_usn}, subject {subject_code}: {total_marks}")
                        continue
                    student_record[subject_code] = total_marks
                    if subject_code not in subject_codes:
                        subject_codes.append(subject_code)

            if len(student_record) > 2:
                records[id_] = student_record
            else:
                print(f"No valid marks for USN {this_usn}")

        if not records:
            print("No valid records processed.")
            return None

        columns = ['USN', 'Student Name'] + subject_codes
        try:
            final_df = pd.DataFrame(records.values())
            if final_df.empty:
                print("Final DataFrame is empty.")
                return None
            for col in columns:
                if col not in final_df.columns:
                    final_df[col] = None
            final_df = final_df[columns]
            print(f"Created DataFrame with {len(final_df)} rows, columns: {columns}")
            return final_df
        except Exception as e:
            print(f"Failed to create final DataFrame: {str(e)}")
            return None

    def create_excel_response(self, df: pd.DataFrame) -> HttpResponse:
        """Create HttpResponse with Excel file for download"""
        if df is None or df.empty:
            print("Cannot generate Excel: DataFrame is empty or None")
            return JsonResponse({"error": "No data available to generate Excel file"}, status=404)

        output = BytesIO()
        sheet_name = 'Sem Results'
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name=sheet_name)
            output.seek(0)
            response = HttpResponse(
                output,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{sheet_name}.xlsx"'
            print("Excel file generated successfully")
            return response
        except Exception as e:
            print(f"Excel generation failed: {str(e)}")
            return JsonResponse({"error": f"Failed to generate Excel: {str(e)}"}, status=500)