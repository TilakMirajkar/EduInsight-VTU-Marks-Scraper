import time
import pandas as pd
import pytesseract
from io import BytesIO
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from PIL import Image
from django.http import HttpResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from .models import Batch, Semester, Subject, Student, Marks


class ResultScraperService:
    def execute_scraping(
        self, prefix_usn: str, usn_range: str, url: str, is_reval: bool
    ) -> Optional[pd.DataFrame]:
        """Execute the complete scraping workflow and return DataFrame."""
        usn_list = self._generate_usn_list(prefix_usn, usn_range)
        driver = self._initialize_webdriver(url)
        try:
            soup_dict = self._scrape_data(driver, usn_list)
            if soup_dict:
                return self._process_data(soup_dict, is_reval)
            print("No data scraped.")
            return None
        except Exception as e:
            print(f"Scraping failed: {str(e)}")
            raise
        finally:
            driver.quit()

    def _generate_usn_list(self, prefix_usn: str, suffix_usn: str) -> List[str]:
        """Generate list of USNs from prefix and range (e.g., '1-3,5')."""
        usn_list = []
        for part in suffix_usn.split(","):
            if "-" in part:
                try:
                    start, end = map(int, part.split("-"))
                    usn_list.extend(
                        f"{prefix_usn}{str(num).zfill(3)}" for num in range(start, end + 1)
                    )
                except ValueError:
                    print(f"Invalid range: {part}")
            else:
                try:
                    num = int(part)
                    usn_list.append(f"{prefix_usn}{str(num).zfill(3)}")
                except ValueError:
                    print(f"Invalid USN suffix: {part}")
        return usn_list

    def _initialize_webdriver(self, url: str) -> webdriver.Chrome:
        """Initialize headless Chrome WebDriver for Railway."""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        print(f"Navigated to {url}")
        return driver

    def _scrape_data(self, driver: webdriver.Chrome, usn_list: List[str]) -> Dict[str, BeautifulSoup]:
        """Scrape data for each USN, handling captchas."""
        soup_dict = {}
        for usn in usn_list:
            retries = 0
            max_retries = 3
            while retries < max_retries:
                try:
                    # Enter USN
                    usn_field = driver.find_element(By.NAME, "lns")
                    usn_field.clear()
                    usn_field.send_keys(usn)

                    # Handle captcha
                    captcha_image = driver.find_element(
                        By.XPATH, '//*[@id="raj"]/div[2]/div[2]/img'
                    ).screenshot_as_png
                    captcha_text = self._get_captcha_from_image(captcha_image)

                    # Enter captcha and submit
                    captcha_field = driver.find_element(By.NAME, "captchacode")
                    captcha_field.clear()
                    captcha_field.send_keys(captcha_text)
                    driver.find_element(By.ID, "submit").click()

                    # Check for alert
                    try:
                        WebDriverWait(driver, 1).until(EC.alert_is_present())
                        alert = driver.switch_to.alert
                        alert_text = alert.text
                        alert.accept()
                        if "University Seat Number is not available or Invalid" in alert_text:
                            print(f"USN {usn} not found. Skipping...")
                            break
                        print(f"Captcha failed for USN {usn}, retrying...")
                        retries += 1
                        continue
                    except:
                        # Success: parse page
                        print(f"Retrieved data for USN {usn}")
                        soup = BeautifulSoup(driver.page_source, "lxml")
                        student_usn = soup.find_all("td")[1].text.split(":")[1].strip().upper()
                        student_name = soup.find_all("td")[3].text.split(":")[1].strip()
                        key = f"{student_usn}+{student_name}"
                        soup_dict[key] = soup
                        driver.back()
                        break

                except Exception as e:
                    print(f"Error for USN {usn}: {str(e)}")
                    retries += 1
                    if retries == max_retries:
                        print(f"Max retries reached for USN {usn}. Skipping...")
                        break
                time.sleep(1)
        return soup_dict

    def _get_captcha_from_image(self, target_image: bytes) -> str:
        """Extract text from captcha image using Tesseract."""
        pixel_range = [(i, i, i) for i in range(102, 130)]
        image_data = BytesIO(target_image)
        image = Image.open(image_data).convert("RGB")
        width, height = image.size
        white_image = Image.new("RGB", (width, height), "white")

        # Filter pixels for OCR
        for x in range(width):
            for y in range(height):
                pixel = image.getpixel((x, y))
                if pixel in pixel_range:
                    white_image.putpixel((x, y), pixel)

        # OCR with Tesseract
        text = pytesseract.image_to_string(white_image, config="--psm 7 --oem 1").strip()
        if len(text) < 6:
            text = text.ljust(6, "A")
        elif len(text) > 6:
            text = text[:6]
        return text

    def _process_data(self, soup_dict: Dict[str, BeautifulSoup], is_reval: bool) -> pd.DataFrame:
        """Process scraped data into DataFrame and save to database."""
        records = {}
        subject_codes = set()
        # Assume semester 1 for simplicity; adjust based on VTU page
        semester, _ = Semester.objects.get_or_create(semester=1)
        # Extract batch year from first USN (e.g., '21' from '1AB21CS')
        batch_year = int(list(soup_dict.keys())[0].split("+")[0][3:5]) + 2000 if soup_dict else 2021
        batch, _ = Batch.objects.get_or_create(batch=batch_year)

        for id_, soup in soup_dict.items():
            this_usn, this_name = id_.split("+")
            # Extract batch year from USN (e.g., '21' → 2021)
            batch_year = int(this_usn[3:5]) + 2000 if len(this_usn) > 4 else 2021
            batch, _ = Batch.objects.get_or_create(batch=batch_year)

            # Extract semester
            semester_div = soup.find("div", style="text-align:center;padding:5px;")
            semester_num = 1  # Default
            if semester_div and "Semester :" in semester_div.text:
                try:
                    semester_num = int(
                        semester_div.text.split("Semester :")[1].strip().split()[0]
                    )
                    if semester_num not in range(1, 9):
                        semester_num = 1
                except (IndexError, ValueError):
                    print(f"Invalid semester for USN {this_usn}. Using default: 1")
            semester, _ = Semester.objects.get_or_create(semester=semester_num)

            # Save student
            student, _ = Student.objects.get_or_create(
                usn=this_usn,
                defaults={"name": this_name, "batch": batch, "semester": semester},
            )
            student_record = {"USN": this_usn, "Student Name": this_name}
            marks_data = semester_div.find_next_sibling("div")
            if not marks_data:
                continue
            rows = marks_data.find_all("div", class_="divTableRow")
            if not rows:
                continue
            data = [
                [cell.text.strip() for cell in row.find_all("div", class_="divTableCell")]
                for row in rows
            ]
            if not data or len(data) < 2:
                continue
            df_temp = pd.DataFrame(data[1:], columns=data[0])

            # Process marks
            for _, row in df_temp.iterrows():
                if "Subject Code" not in row or "Total" not in row:
                    continue
                subject_code = row["Subject Code"]
                total_marks = row["Total"]
                if not total_marks.isdigit():
                    continue  # Skip invalid marks
                # Save subject and marks to DB
                subject, _ = Subject.objects.get_or_create(
                    name=subject_code, semester=semester
                )
                Marks.objects.get_or_create(
                    student=student,
                    subject=subject,
                    semester=semester,
                    defaults={"marks": int(total_marks)},
                )
                student_record[subject_code] = total_marks
                subject_codes.add(subject_code)

            records[id_] = student_record

        if not records:
            print("No records processed.")
            return pd.DataFrame()

        # Create DataFrame
        columns = ["USN", "Student Name"] + sorted(subject_codes)
        final_df = pd.DataFrame(records.values())
        for col in columns:
            if col not in final_df.columns:
                final_df[col] = None
        final_df = final_df[columns]
        return final_df

    def create_excel_response(self, df: pd.DataFrame) -> HttpResponse:
        """Generate Excel file from DataFrame for download."""
        output = BytesIO()
        try:
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Sem Results", chunksize=100)
            output.seek(0)
            response = HttpResponse(
                output,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = 'attachment; filename="Sem_Results.xlsx"'
            response["X-Response-Type"] = "file"
            return response
        except Exception as e:
            print(f"Excel generation failed: {str(e)}")
            raise