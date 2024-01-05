from math import e
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
import time
import datetime;
import xlsxwriter
from googletrans import Translator
import re
# Import libraries
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import time
import phonenumbers
from transformers import BertTokenizer, BertForSequenceClassification
from torch.nn.functional import softmax
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, parse_qs
from sqlalchemy import create_engine
import sqlalchemy
from Social.src.configurations import settings

from Social.src.configurations.settings import PostgreSQL_Connection


from datetime import datetime as datetimeDatabase
class getDataFromExcelInsertIntoDatabase:
    
    def split_name(self, row):
        name = row['Names'].strip().split(' ')
        listData = [' ',' ',' ']
        if len(name)==1:
            listData[0] = name[0]
        if len(name)==2:
            listData[0] = name[0]
            listData[1] = name[1]
        if len(name)==3:
            listData[0] = name[0]
            listData[1] = name[1]
            listData[2] = name[2]
        print(listData)
        return pd.Series(listData, index=['first_name', 'last_name', 'middle_name'])
        #return listData[0],listData[1],listData[2]
    # Function to extract user_id from the URL
    # Get the user_id from the facebook profile URL
    def extract_user_id(self, row):
        url = row['Profile URLo']
        parsed_url = urlparse(url)
        
        path_segments = parsed_url.path.split('/')
        userIDCheck = path_segments[1] if len(path_segments) > 1 else None
        if userIDCheck=='profile.php':
            query_params = parse_qs(parsed_url.query)
            print(query_params)
            user_id = query_params.get('id', [None])[0]  # None if 'user_id' not found
            return user_id
        else:
            if ".php" in userIDCheck:
                return False
            else:
                userIDCheck = userIDCheck.strip()
                return str(userIDCheck)

    def insertData(self,fileName):
        engine = create_engine(PostgreSQL_Connection)

        #print("data/facebook/"+fileName)
        df = pd.read_excel("data/facebook/"+fileName)
        df_post = df.drop_duplicates(subset=['Post']) 
        df['Lives city'] = df['Lives city'].str.title()
        df['Lives state'] = df['Lives state'].str.title()
        df['Lives Country'] = df['Lives Country'].str.title()
        df['From City'] = df['From City'].str.title()
        df['From State'] = df['From State'].str.title()
        df['From Country'] = df['From Country'].str.title()

        userData = df.drop_duplicates(subset=['Names'])
        userData['email_id'] = userData.apply(self.extract_user_id, axis=1)
        
        userData[['first_name', 'last_name', 'middle_name']] = userData.apply(lambda row: self.split_name(row), axis=1)
        userData['dob']=''
        userData['profile_img']=''
        
        # Get the current date and time
        current_datetime = datetimeDatabase.now()
        # Format the datetime object as a string
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        userData['created_on']=str(formatted_datetime)
        userData['unique_identity']=str(current_datetime)
        userData['created_by']='Admin'
        userData = userData.fillna('')
        
        ################### Create a dataframe for user
        userDataFrame = {
            "email_id":userData['email_id'].tolist(),
            "first_name":userData['first_name'].tolist(),
            "last_name":userData['last_name'].tolist(),
            "middle_name":userData['middle_name'].tolist(),
            "contact":userData['Cell No'].tolist(),
            "dob":["null"]*len(userData['Cell No'].tolist()),
            "profile_img" : ["/assets/img/avatars/6.jpg"]*len(userData['Cell No'].tolist()),
            "state_code" : userData['Lives state'].tolist(),
            "behaviour_type" : userData['Anti/Pro'].tolist(),
            "profile_url" : userData['Profile URLo'].tolist(),
            "score" : userData['Sentiment Score'].tolist(),
            "created_on" : userData['created_on'].tolist(),
            "created_by" : userData['created_by'].tolist()
        }

        userDataFrameDF = pd.DataFrame(userDataFrame)
        # Drop duplicates based on the 'column_name' column
        userDataFrameDF = userDataFrameDF.drop_duplicates(subset='email_id', keep='first')
        print("Before merge",userData['email_id'])
        #check user exist into database
        existing_data = pd.read_sql('SELECT email_id FROM platform_users', con=engine)
        filterd_user_data = userDataFrameDF[~userDataFrameDF['email_id'].isin(existing_data['email_id'])]
        #Plateform user dataFrame
        print("Plate form user",existing_data)
        print("PlateForm User DataFrame",filterd_user_data)
        time.sleep(30)
        # Check if there is any new data to append
        if not filterd_user_data.empty:
            filterd_user_data.to_sql('platform_users', con=engine, index=False, if_exists='append')

        ################### Post Data Insert into database #################
        
        # Create a dataframe for post
        postDataFrame = {
            "page_id":[1]*len(userData['Post'].tolist()),
            "post_content":userData['Post'].tolist(),
            "classification" : userData['Anti/Pro'].tolist(),
            "score" : userData['Sentiment Score'].tolist(),
            "created_on" : userData['created_on'].tolist(),
            "created_by" : userData['created_by'].tolist()
        }

        postDataFrameDF = pd.DataFrame(postDataFrame)
        # Drop duplicates based on the 'column_name' column
        postDataFrameDF = postDataFrameDF.drop_duplicates(subset='post_content', keep='first')


        #check post exist into database
        existing_data = pd.read_sql('SELECT post_content FROM posts', con=engine)
        filterd_post_data = postDataFrameDF[~postDataFrameDF['post_content'].isin(existing_data['post_content'])]

        # Check if there is any new data to append
        if not filterd_post_data.empty:
            filterd_post_data.to_sql('posts', con=engine, index=False, if_exists='append')

        ################### Create a dataframe for comment  

        postDataFrameDF = {
            #"post_id":["null"]*len(userData['email_id'].tolist()),
            "email_id":userData['email_id'].tolist(),
            "post_content":userData['Post'].tolist(),
            "comment_content":userData['Comments'].tolist(),
            "created_on" : userData['created_on'].tolist(),
            "created_by" : userData['created_by'].tolist(),
            "user" : userData['Sentiment Score'].tolist(),
            "score" : userData['Sentiment Score'].tolist(),
            "classification" : userData['Anti/Pro'].tolist(),
            "score" : userData['Sentiment Score'].tolist(),
            "comment_url" : userData['Profile URLo'].tolist()
        }
        postDataFrameDF = pd.DataFrame(postDataFrameDF)
        # Assuming postDataFrameDF is your DataFrame with post_content

        existing_data = pd.read_sql('SELECT post_content, post_id FROM posts', con=engine)
        
        # Ensure postDataFrameDF is a DataFrame
        if not isinstance(postDataFrameDF, pd.DataFrame):
            raise TypeError("postDataFrameDF should be a pandas DataFrame")

        # Ensure existing_data is a DataFrame
        if not isinstance(existing_data, pd.DataFrame):
            raise TypeError("existing_data should be a pandas DataFrame")

        # Ensure 'post_content' column is present in both DataFrames
        if 'post_content' not in postDataFrameDF.columns or 'post_content' not in existing_data.columns:
            raise ValueError("Both DataFrames should have a 'post_content' column")

        # Merge the existing_data into postDataFrameDF based on 'post_content'
        merged_data = pd.merge(postDataFrameDF, existing_data, how='left', on='post_content')
        print(merged_data)
        # Drop the 'existing_post_id' column if you don't need it
        merged_data = merged_data.drop(columns=['post_content'])


        #check post exist into database
        existing_comment_data = pd.read_sql('SELECT comment_content FROM comments', con=engine)
        merged_data = merged_data[~merged_data['comment_content'].isin(existing_comment_data['comment_content'])]
        print("Comment Merge Data",merged_data)
        # Check if there is any new data to append
        if not merged_data.empty:
            merged_data.to_sql('comments', con=engine, index=False, if_exists='append')
            print('Data Is Inserted')

class prepareFinalExclsheet:

    #Define function to translate hindi lang to English lang, 
    #Return english senetence
    def hindToEnglish(self,sent):
        max_retries=3
        translator = Translator()
        hindi_sentence = sent
        for retry in range(max_retries):
            try:
                english_sentence = translator.translate(hindi_sentence, dest='en').text
                return english_sentence
            except:
                print(f"Translation request timed out ")
                time.sleep(3)  # Wait for a few seconds before retrying

    # Define function to get sentiment
    def get_sentiment(self,text):
    
        # Load pre-trained DistilBERT model and tokenizer
        # Use a smaller DistilBERT model for faster inference
        model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Tokenize text
        encoded_text = tokenizer.encode_plus(text, return_tensors='pt')

        # Get sentiment prediction 
        output = model(**encoded_text)
        scores = output[0][0].detach().numpy()
        scores = torch.nn.functional.softmax(torch.tensor(scores), dim=0)
        print("dsarsadf saddddddddd",scores)
        # Get sentiment label
        label = 'Positive_'+str(scores[1]) if scores[1] > scores[0] else 'Negative_'+str(scores[0])

        return label

    #Define function to scrap profile overview data, It's taking driver and profile URL as parameter
    #Return overview data
    def scrap_overview(self,driver,profileName):
        driver.get(profileName)
        wait = WebDriverWait(driver, 20)

        # Find the span element by its text content using JavaScript
        span_text = "About"  # Replace with the actual text you want to click
        js_script = f"var spans = document.querySelectorAll('span'); for (var span of spans) {{ if (span.textContent === '{span_text}') {{ span.click(); }} }}"
        driver.execute_script(js_script)
        sleep(2)

        # Find the span element by its text content using JavaScript
        span_text = "Overview"  # Replace with the actual text you want to click
        js_script = f"var spans = document.querySelectorAll('span'); for (var span of spans) {{ if (span.textContent === '{span_text}') {{ span.click(); }} }}"
        driver.execute_script(js_script)
        sleep(2)

        #Get profile overview data and concatinate those data
        frd_overview = ''
        friendLIst_overview = driver.find_elements(By.XPATH,"//div[@class='x1hq5gj4']")
        for friendMT in friendLIst_overview:
            frd_overview +=friendMT.text+'\n' 
            friendLIst_overview = driver.find_elements(By.XPATH,"//div[@class='x1hq5gj4']")

        friendLIst_overview = driver.find_elements(By.XPATH,"//div[@class='xat24cr']")
        
        for friendMT in friendLIst_overview:
            frd_overview+=frd_overview+friendMT.text+'\n'

        return frd_overview    

    #Define function to, Extract city, state, country from overview profile data and return as a disknary 
    def extract_lives_in(self,text):

        #======== Extract Data from Lives in ============

        # Define a regular expression pattern to match lines starting with "Lives in"
        pattern = r'^Lives in.*$'
        
        # Use the re.MULTILINE flag to match lines in a multiline text
        matches = re.findall(pattern, text, flags=re.MULTILINE)
        current_state=['delhi','andaman and nicobar islands','chandigarh','puducherry','daman and diu and dadra and nagar haveli','lakshadweep','jammu and kashmir','ladakh','andhra pradesh','assam','arunachal pradesh','bihar','chhattisgarh','gujarat','goa','himachal pradesh','haryana','jharkhand','kerala','karnataka','maharashtra','madhya pradesh','manipur','mizoram','mizoram','nagaland','odisha','punjab','rajasthan','sikkim','tamil nadu','telangana','tripura','west bengal','uttarakhand','uttar pradesh']
        # Extract and return the first match (if any)
        #first index - city
        #second index - state
        #third index - Country
        lives_in = list((" "," "," "))
        lives_from_data = dict()
        if matches:
            filterText = matches[0].replace('Lives in',"")
            livesData = filterText.split(',')
            print("Lived Data",livesData)
            if len(livesData)>2:
                lives_in[0] = livesData[0]
                lives_in[1] = livesData[1]
                lives_in[2] = livesData[2]
            elif len(livesData)==2:
                lives_in[0] = livesData[0]
                Livest = livesData[0].lower()
                if Livest.strip() in current_state:
                    lives_in[1] = livesData[0]
                    lives_in[0] = ''
                print(livesData[1])
                lives_in[2] = livesData[1]
                stlive = livesData[1].lower()
                if stlive.strip() in current_state:
                    lives_in[1] = livesData[1]
                    lives_in[2] = ''
                
            elif len(livesData)==1:
                lives_in[0] = livesData[0]

            print("Lives in",lives_in)
        #================================ Extract Data from location =====================

        # Define a regular expression pattern to match lines starting with "Lives in"
        pattern = r'^From.*$'
        
        # Use the re.MULTILINE flag to match lines in a multiline text
        matches = re.findall(pattern, text, flags=re.MULTILINE)
        
        # Extract and return the first match (if any)
        #first index - city
        #second index - state
        #third index - Country
        from_in = list((" "," "," "))
        
        if matches:
            filterText = matches[0].replace('From',"")
            fromData = filterText.split(',')
            print("form data",fromData)
            if len(fromData)==3:
                from_in[0] = fromData[0]
                from_in[1] = fromData[1]
                from_in[2] = fromData[2]
            elif len(fromData)==2:
                from_in[0] = fromData[0]
                st = fromData[0].lower()
                if st.strip() in current_state:
                    from_in[1] = fromData[0]
                    from_in[0] = ''

                from_in[2] = fromData[1]
                stst = fromData[1].lower()
                if stst.strip() in current_state:
                    from_in[1] = fromData[1]
                    from_in[2] = ''

                
            elif len(fromData)==1:
                from_in[0] = fromData[0]

        #==========================================Phone Number Get=========================
        phone=''
        for match in phonenumbers.PhoneNumberMatcher(text, "IN"):
            phone = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164)
        print("pppppppp",phone)
        print("From Data",from_in)
        lives_from_data['cellNo']=phone
        lives_from_data['livesIn']=lives_in
        lives_from_data['fromIn']=from_in
        
        return lives_from_data
    def dataPutIntoDatabase(self, driver, filesName):
        print(filesName)
        # Create a new Excel workbook and add a worksheet.
        workbook = xlsxwriter.Workbook("data/facebook/output_"+filesName)
        worksheet = workbook.add_worksheet()
        
        # Write data to the worksheet.

        worksheet.write('A1', 'Post')
        worksheet.write('B1', 'Comments')
        worksheet.write('C1', 'Names')
        worksheet.write('D1', 'Lives city')

        worksheet.write('E1', 'Lives state')
        worksheet.write('F1', 'Lives Country')
        worksheet.write('G1', 'From City')
        worksheet.write('H1', 'From State')
        worksheet.write('I1', 'From Country')
        worksheet.write('J1', 'Cell No')
        
        worksheet.write('K1', 'Anti/Pro')
        worksheet.write('L1', 'Sentiment Score')
        worksheet.write('M1', 'Profile URLo')

        # Close the workbook to save it.
        workbook.close()


        df = pd.read_excel("data/facebook/"+filesName)
        post = list()
        comment = list()
        name = list()
        anti_pro = list()
        lives_city= list()
        lives_state= list()
        lives_country= list()
        from_city= list()
        from_state= list()
        from_country= list()
        cell_no = list()
        sentiment_score = list()
        profile_url = list()
        # Iterate Through Rows
        for index, row in df.iterrows():
            try:
                # Access row data by column name
                posts = row['Post']
                comments = row['Comment']
                comments = comments.replace('·','')
                comments = comments.strip()
                
                match = re.search(r'\d+', comments[::-1])
                if match:
                    last_integer = match.group()[::-1]  # Reverse the matched string to get the last integer
                    position = len(comments) - match.end()  # Calculate the position of the last integer

                    print(f"Last integer: {last_integer}")
                    print(f"Position: {position}")
                    print(comments[0:position])
                    comments = comments[0:position]
                else:
                    comments = row['Comment']

                names = row['Name']
                href = row['Href']
                
                post.append(posts)
                name.append(names)
                comment.append(comments)
                profile_url.append(href)
                # Wait for the element to be present
                wait = WebDriverWait(driver, 20)
                sleep(4)
                """
                Sr. Manager at OnSumaye
                Shared with Public

                Studied Informatica at MNNIT, Allahabad, India
                Shared with Your friends

                Lives in Biposi Najafgarh, Uttar Pradesh, India
                Shared with Public

                From Ambedkar Nagar, India
                Shared with Public

                Single
                Shared with Your friends

                085879 96347
                """
                profileOverview = self.scrap_overview(driver,href)
                #{'cellNo': '+918587996347', 'livesIn': [' Biposi Najafgarh', ' Uttar Pradesh', ' India'], 'fromIn': [' Ambedkar Nagar', ' ', ' India']}
                csc = self.extract_lives_in(profileOverview)
                print(csc)
                lives_city.append(csc['livesIn'][0] if csc['livesIn'][0] else ' ')
                lives_state.append(csc['livesIn'][1] if csc['livesIn'][1] else ' ')
                lives_country.append(csc['livesIn'][2] if csc['livesIn'][2] else ' ')
                from_city.append(csc['fromIn'][0] if csc['fromIn'][0] else ' ')
                from_state.append(csc['fromIn'][1] if csc['fromIn'][1] else ' ')
                from_country.append(csc['fromIn'][2] if csc['fromIn'][2] else ' ')
                cell_no.append(csc['cellNo'] if csc['cellNo'] else ' ')

                #arg= 'नमस्ते, कैसे हो?'
                if comments:
                    #comment_english =  self.hindToEnglish(comments)
                    comment_english = comments
                else:
                    comment_english = 'None'

                if comment_english is None:
                    pass

                # Define sentiment labels
                sentiment_labels = ["Negative", "Neutral", "Positive"]

                print('Above senti')
                #'Positive' if scores[1] > scores[0] else 'Negative'
                pos_neg_comment = self.get_sentiment(comment_english)
                print("Below sentiment")

                # Anti Government or Pro Government
                print(pos_neg_comment)
                scoreList = pos_neg_comment.split('_')
                scoreNo = re.findall("\d+\.\d+", scoreList[1])

                print(f"convert string float to float {float(scoreNo[0])}")
                if scoreList[0].strip()=='Positive':
                    if float(scoreNo[0]) > 0.9000:
                        antPro = 'Pro Government'
                    else:
                        antPro = 'Anti Government'    
                else:
                    if float(scoreNo[0]) > 0.9000:
                        antPro = 'Anti Government'
                    else:
                        antPro = 'Pro Government'

                #antPro = scoreList[0].strip()
                #antPro = sentiment_labels[predicted_label]
                anti_pro.append(antPro)
                
                sentiment_score.append(scoreNo[0])
                #print(f"Row {index + 1}: {post}, {Comment}, {name}")
                

                # initialize data of lists.
                data = {'Post': post,
                        'Comments':comment,
                        'Names':name,
                        'Lives city':lives_city,
                        'Lives state' : lives_state,
                        'Lives Country' : lives_country,
                        'From City':from_city,
                        'From State':from_state,
                        'From Country':from_country,
                        'Cell No':cell_no,
                        'Anti/Pro':anti_pro,
                        'Sentiment Score':sentiment_score,
                        'Profile URL':profile_url
                        }
                print(data)
                print("=============")
                # Create DataFrame
                #df = pd.DataFrame(data)

                # Print the output.
                #print(df)
                #df.to_excel("final_570_bjp_outer.xlsx")

                # read the demo2.xlsx file
                #df=pd.read_excel("nm.xlsx")
                #data = {'Name': ['Tom4', 'Joseph4', 'Krish4', 'John4'], 'Age': [22, 221, 19, 18]}
                print("above done")
                df = pd.DataFrame(data)
                print(df)
                print("Below done")
                # appending the data of df after the data of demo1.xlsx
                with pd.ExcelWriter("data/facebook/output_"+filesName,mode="a",engine="openpyxl",if_sheet_exists="overlay") as writer:
                    df.to_excel(writer, sheet_name="Sheet1",header=None, startrow=writer.sheets["Sheet1"].max_row,index=False)
                    print('Done')
                del post[:]
                del comment[:]
                del name[:]
                del lives_city[:]
                del lives_state[:]
                del lives_country[:]
                del from_city[:]
                del from_state[:]
                del from_country[:]
                del cell_no[:]
                del anti_pro[:]
                del sentiment_score[:]
                del profile_url[:]
            except:
                del post[:]
                del comment[:]
                del name[:]
                del lives_city[:]
                del lives_state[:]
                del lives_country[:]
                del from_city[:]
                del from_state[:]
                del from_country[:]
                del cell_no[:]
                del anti_pro[:]
                del sentiment_score[:]
                del profile_url[:]
                pass

class facebookScrap(prepareFinalExclsheet,getDataFromExcelInsertIntoDatabase):
    def login(self,email,password):
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

       # driver = webdriver.Chrome(options=chrome_options)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        driver = webdriver.Chrome()  # Replace with the appropriate WebDriver for your browser
        # Create a new ChromeDriver instance
        

        driver.get("https://www.facebook.com")
        driver.maximize_window()
        email_input = driver.find_element(By.ID, "email")
        password_input = driver.find_element(By.ID, "pass")
        login_button = driver.find_element(By.NAME, "login")

        email_input.send_keys(email)
        password_input.send_keys(password)
        login_button.click()
        return driver

        
    # First Step
    # By this function we can scrape post data, name, comments and url from POST html raw data
    # Save this data into excel file
    def scrap_post_name_comment_url(self,driver,html_content,fileName):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find elements by class name and extract data
            elements_with_class = soup.find_all(attrs={'data-ad-preview': 'message'})
            print(f"post connete {elements_with_class}")
            print(type(elements_with_class))
            print("===== Neeraj Maurya ======")
            
            #post_msg = elements_with_class[0].text
            postMsg = soup.find_all('div', style=lambda value: value and 'text-align: start' in value)

            post_msg = postMsg[0].text
            ##############################Post Content######################################

            # Find elements by attribute and extract data
            elements_with_attribute = soup.find_all(attrs={'role': 'article'})

            href_link = list()
            name = list()
            comment = list()
            postMsg = list() 
            for element in elements_with_attribute:

                ##############################Post Comment######################################
                print("Comment of post in popup",element.text)

                anchor_tags = element.find_all('a')
                for anchor in anchor_tags:

                    ##############################Comment User Name #############################
                    text = anchor.text

                    ##############################Profile URL #############################
                    href = anchor['href']

                    if len(text.replace(" ", ""))>3:
                        ##############################Fileter Out Comment #############################
                        commentText = element.text
                        Commentonmessage = commentText.lower()
                        Commentonmessage = Commentonmessage.replace(text.lower(),'')
                        Commentonmessage = Commentonmessage.replace('Follow'.lower(),'')
                        Commentonmessage = Commentonmessage.replace('LikeReply'.lower(),'')
                        Commentonmessage = Commentonmessage.replace('Top fan'.lower(),'')
                        if 'facebookfacebookfacebook' in Commentonmessage:
                            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                            continue
                        comment.append(Commentonmessage)
                        postMsg.append(post_msg)
                        name.append(text)
                        href_link.append(href)
                        print(f"Anchor Text: {text}")
                        print(f"Href Tag:{href}")

            data = {
                "Post":postMsg,  
                "Comment": comment,
                "Name": name,
                "Href": href_link
            }
            ct = datetime.datetime.now()
            ts = ct.timestamp()
            #load data into a DataFrame object:
            #df = pd.DataFrame(data)

            df = pd.DataFrame(data)
            # appending the data of df after the data of demo1.xlsx
            with pd.ExcelWriter('data/facebook/'+fileName,mode="a",engine="openpyxl",if_sheet_exists="overlay") as writer:
                df.to_excel(writer, sheet_name="Sheet1",header=None, startrow=writer.sheets["Sheet1"].max_row,index=False)
                print("Data Inserted into Excel Sheet")
            print(df)
        except Exception as error:
           sleep(3)
           print("scrap_user_html_content:", error) # An error occurred: name 'x' is not defined 

    # First Step:
    # This function is responsible for loading dynamic pages and reading post data and commenting
    # Make dynamic excel file
    # Pass post popup html data into scrap_post_name_comment_url
    def scrap_post(self,driver,page,pageName,noOfPage):
        
        sleep(5)
        driver.get(page)
        
        timestr = time.strftime("%Y%m%d-%H%M%S")
        fileName = pageName+timestr+'.xlsx'
        
        # Create a new Excel workbook and add a worksheet.
        workbook = xlsxwriter.Workbook("data/facebook/"+fileName)
        worksheet = workbook.add_worksheet()
        
        # Write data to the worksheet.

        worksheet.write('A1', 'Post')
        worksheet.write('B1', 'Comment')
        worksheet.write('C1', 'Name')
        worksheet.write('D1', 'Href')

        # Close the workbook to save it.
        workbook.close()
        print("Page Title=>", driver.title)
        #wait = WebDriverWait(driver, 20)

        # Filter the span elements to only include those which contain "View more comments".
        postOfPost = []
        i=0
        while i< int(noOfPage):
            i+=1
            sleep(5)
            wait = WebDriverWait(driver, 10)  # Increase the waiting time here (in seconds)
            element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x1yztbdb') and contains(@class, 'x1n2onr6') and contains(@class, 'xh8yej3') and contains(@class, 'x1ja2u2z')]")))
            # span_elements = driver.find_elements(By.XPATH, "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']")
            span_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'x1yztbdb') and contains(@class, 'x1n2onr6') and contains(@class, 'xh8yej3') and contains(@class, 'x1ja2u2z')]")
            
            for span_element in span_elements:
                try:
                    ########################### Click On View More Comments ############################
                    
                    wait = WebDriverWait(driver, 10)
                    view_more_comments_span = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'View more comments')]")))

                    # if view_more_comments_span:
                    #     action = ActionChains(driver)
                    #     action.move_to_element(view_more_comments_span).click().perform()
                    # else:
                    #     pass

                    sleep(10)
                    view_more_comments_button = span_element.find_element(By.XPATH, ".//span[contains(text(),'View more comments')]")
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//span[contains(text(),'View more comments')]")))
                    view_more_comments_button.click()

                    sleep(5)
                                    
                    wait = WebDriverWait(driver, 20)  # Increase the waiting time here (in seconds)
                    element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog' and @aria-labelledby]")))
                                            
                    popup_element = driver.find_element(By.XPATH, "//div[@role='dialog' and @aria-labelledby]")
                    print("Parent popupd",popup_element.text)

                    outer_html = popup_element.get_attribute("outerHTML")
                    print("=====================")

                    soup = BeautifulSoup(outer_html, 'html.parser')
                    #post_msg = elements_with_class[0].text
                    postMsg = soup.find_all('div', style=lambda value: value and 'text-align: start' in value)
                    post_msg = postMsg[0].text
                    print("Testing here = >",post_msg)
                    print("Post List",postOfPost)
                    
                    self.scrap_post_name_comment_url(driver,outer_html,fileName)
                    
                    backButton = driver.find_elements(By.XPATH, "//div[@aria-label='Close']")
                    action = ActionChains(driver)
                    action.move_to_element(backButton[0]).click().perform()
                    sleep(5)

                    print("After scrape user html content")
                    sleep(2)
                        ################################ Close Popup ########################################
                        #popup_element = driver.find_element(By.XPATH, "//div[@aria-label='Close']")
                        #popup_element.click()
                        #sleep(2)
                except Exception as error:
                    print("scrap_popup_html:", error) # An error occurred: name 'x' is not defined
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        return fileName

