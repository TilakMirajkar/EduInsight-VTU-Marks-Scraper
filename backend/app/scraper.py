import time
import pandas as pd
import pytesseract

from io import BytesIO
from bs4 import BeautifulSoup
from PIL import Image
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from django.http import HttpResponse


class ResultScraperService:
    def __init__(self):
        self.tesseract_path = r'Tesseract-OCR/tesseract.exe'
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
    
    def execute_scraping(self, prefix_usn, usn_range, url, is_reval):
        """Main method to execute the complete scraping workflow"""

        usn_list = self._generate_usn_list(prefix_usn, usn_range)
        driver = self._initialize_webdriver(url)
        
        try:
            soup_dict = self._scrape_data(driver, usn_list)
            if soup_dict:
                return self._process_data(soup_dict, is_reval)
            return None
        finally:
            driver.quit()
    
    def _generate_usn_list(self, prefix_usn, suffix_usn):
        """Generate list of USNs based on prefix and range"""
        usn_list = []
        for part in suffix_usn.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                usn_list.extend(f"{prefix_usn}{str(num).zfill(3)}" for num in range(start, end + 1))
            else:
                usn_list.append(f"{prefix_usn}{str(int(part)).zfill(3)}")
        return usn_list
    
    def _initialize_webdriver(self, url):
        """Initialize and return a configured webdriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        return driver
    
    def _scrape_data(self, driver, usn_list):
        """Scrape data for each USN in the list"""
        soup_dict = {}
        for usn in usn_list:
            while True:
                try:
                    # Clear and enter USN
                    driver.find_element(By.NAME, 'lns').clear()
                    driver.find_element(By.NAME, 'lns').send_keys(usn)
                    
                    # Handle captcha
                    captcha_image = driver.find_element(By.XPATH, '//*[@id="raj"]/div[2]/div[2]/img').screenshot_as_png
                    captcha_text = self._get_captcha_from_image(captcha_image)
                    
                    # Enter captcha and submit
                    driver.find_element(By.NAME, 'captchacode').clear()
                    driver.find_element(By.NAME, 'captchacode').send_keys(captcha_text)
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
                        
                        print(f"Captcha failed for USN {usn}")
    
                    
                    except:
                        # No alert means success
                        print(f"Successfully retrieved data for USN {usn}")
                        soup = BeautifulSoup(driver.page_source, 'lxml')
                        
                        # Extract student info
                        student_usn = soup.find_all('td')[1].text.split(':')[1].strip().upper()
                        student_name = soup.find_all('td')[3].text.split(':')[1].strip()
                        key = f'{student_usn}+{student_name}'
                        
                        soup_dict[key] = soup
                        driver.back()
                        break
                
                except Exception as e:
                    print(f"Error processing USN {usn}: {str(e)}")

            
            time.sleep(1)
        
        return soup_dict
    
    def _get_captcha_from_image(self, target_image):
        """Extract text from captcha image"""
        # Pixel range for text extraction
        pixel_range = [(i, i, i) for i in range(102, 130)]
        
        # Load and process image
        image_data = BytesIO(target_image)
        image = Image.open(image_data)
        width, height = image.size
        image = image.convert("RGB")
        white_image = Image.new("RGB", (width, height), "white")
        
        # Filter pixels
        for x in range(width):
            for y in range(height):
                pixel = image.getpixel((x, y))
                if pixel in pixel_range:
                    white_image.putpixel((x, y), pixel)
        
        # Extract text using OCR
        text = pytesseract.image_to_string(white_image, config='--psm 7 --oem 1').strip()
        
        # Ensure text is exactly 6 characters
        if len(text) < 6:
            text = text.ljust(6, 'A')
        elif len(text) > 6:
            text = text[:6]
        
        return text
    
    def _process_data(self, soup_dict, is_reval):
        """Process the scraped data into a structured DataFrame"""
        records = {}
        subject_codes = []
        
        for id, soup in soup_dict.items():
            this_usn, this_name = id.split('+')
            
            # Find semester data
            sems_divs = soup.find_all('div', style="text-align:center;padding:5px;")
            if not sems_divs:
                continue
                
            first_sem_div = sems_divs[0]
            sems_data = [first_sem_div.find_next_sibling('div')]
            
            student_record = {'USN': this_usn, 'Student Name': this_name}
            
            # Process each semester's marks
            for marks_data in sems_data:
                rows = marks_data.find_all('div', class_='divTableRow')
                if not rows:
                    continue
                    
                data = [[cell.text.strip() for cell in row.find_all('div', class_='divTableCell')] for row in rows]
                if not data or len(data) < 2:
                    continue
                    
                df_temp = pd.DataFrame(data[1:], columns=data[0])
                
                # Extract marks for each subject
                for _, row in df_temp.iterrows():
                    if 'Subject Code' not in row or 'Total' not in row:
                        continue
                        
                    subject_code = row['Subject Code']
                    total_marks = row['Total']
                    
                    student_record[subject_code] = total_marks
                    
                    if subject_code not in subject_codes:
                        subject_codes.append(subject_code)
            
            records[id] = student_record
        
        if not records:
            return pd.DataFrame()
            
        # Create final DataFrame
        columns = ['USN', 'Student Name'] + subject_codes
        final_df = pd.DataFrame(records.values())
        
        # Ensure all columns exist
        for col in columns:
            if col not in final_df.columns:
                final_df[col] = None
                
        # Reorder columns
        final_df = final_df[columns]
        
        return final_df
    
    def create_excel_response(self, df):
        """Create HttpResponse with Excel file for download"""
        output = BytesIO()
        sheet_name = f'Sem Results'
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        
        output.seek(0)
        
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{sheet_name}.xlsx"'
        
        return response