#no2 files in the venv folder are not getting read
from bs4.element import SoupStrainer
import  requests as rq
from bs4 import BeautifulSoup
# import psycopg2
import re
# from functools import cache  # CANT USE UNLESS UPDATE TO 3.9 Python


#If using Windows, use Task Scheduler App to customize when you want the app to run
#pretty much done just update it and stuff
SEC_APIs = {'Concept': 'https://data.sec.gov/api/xbrl/companyconcept/CIK##########/us-gaap/AccountsPayableCurrent.json',
            'Facts': 'https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json',
            'XBRL Frames': 'https://data.sec.gov/api/xbrl/frames/us-gaap/AccountsPayableCurrent/USD/CY2019Q1I.json'}
            
token = "https://api.xbrl.us/oauth2/token"  
search = 'https://api.xbrl.us/api/v1/'  

headers = {
    'Authorization': 'TOKEN <MY_TOKEN>'
}

entity_points = ('entity/{entity.id}/report/search?', 'entity/report/search?', 'entity/')
report_points = ('report/search?', 'report/report.id}', 'report/{report.id}/fact/search?', 'report/fact/search?')
fact_points = ('fact/search', 'fact/oim/search', 'fact/{fact.id}')
fields= "&fields=report.sec-url" # ',object.property' when adding to field string. No kwargs allowed in field string


TNT = {}

def loginXBRL(**kwargs):
    """Kwargs name have to be EXACTLY the same as the one listed in the documentation"""
    access = rq.post(token, json=kwargs).json()
    print(access)
    access_token  = access["access_token"] 
    TNT[access_token] , TNT[access['refresh_token']]= access['expires_in'], access['refresh_token_expires_in']
    headers['Authorization'] = f'Bearer {access_token}'  
    return headers 
      


#add time here. pair refresh token and auth token with thier times

class Report:   
    """Enter and Exit methods:used with 'with' and to eventually parse into other documentation.
    Using XBRL API"""
    # __slots__ = ['name','doctype','curr','cik','ticker','sourcelinks']

    def __init__(self, name=None,cik=None,ticker=None,doctype='10-K'): #use date module to get the current year or something like that
        """Get SIC from: https://www.sec.gov/corpfin/division-of-corporation-finance-standard-industrial-classification-sic-code-list
        Get current reports """
        # self.__slots__= None
        self.name = name
        self.cik = cik
        self.ticker = ticker 
        self.doctype = f'&report.document-type={doctype}'
        self.curr = '&report.is-most-current=true' #this does not work in with the url for some reason report.is-most-current=true&
        self.sourcelinks = []

    def find(self,timeout=None):
        '''While logged in. Or if token is refreshed
        Get the report URL fron the JSON.
        Learn Postgres to store in a database 
        UPDATE:Gui with JavaScript'''
        #report.sic-code = 'SIC CODE'
        securl = None 

        if self.name is not None and self.cik is None and self.ticker is None:
            print(f"GETTING:{search}{entity_points[1]}entity.name={self.name}{self.doctype}{fields}")  
            query=rq.get(f'{search}{entity_points[1]}entity.name={self.name}{self.doctype}{fields}',headers=headers)
            
            
        elif self.name is None and self.ticker is None and self.cik is not None:
            print(f"GETTING:{search}{entity_points[1]}entity.cik={self.cik}{self.doctype}{fields}")    
            query=rq.get(f'{search}{entity_points[1]}entity.cik={self.cik}{self.doctype}{fields}',headers=headers)
            

        elif self.name is None and self.cik is None and self.ticker is not None:
            print(f"GETTING:{search}{entity_points[1]}entity.ticker={self.ticker}{self.doctype}{fields}")
            query=rq.get(f'{search}{entity_points[1]}entity.ticker={self.ticker}{self.doctype}{fields}',headers=headers)

        else:
            raise RuntimeError('Need one to query. CIK or Entity Name or Ticker.')

        securl = query.json()['data']
        urls=[]
       
        for url in securl[0]['report']['data']:
            urls.append(url['report.sec-url'])
        #set user agent header  and delete Authorization  key
        # id=lambda x: x and x.startswith('menu_cat') REMEMBER THIS SYNTAX'
        del headers['Authorization']
        headers['User-agent'] = "Devin's Personal Finance ProgramName https://devinportwebsite.herokuapp.com/" 
        page=rq.get(urls[0],headers=headers) #query most current but string does not work
        soup=BeautifulSoup(page.text,'html.parser')
        
        databtn = soup.find('a',attrs={'href':True,'id':'interactiveDataBtn'}).get('href')
        decon_10k = rq.get('https://www.sec.gov/'+ databtn)
        page = BeautifulSoup(decon_10k.text,'html.parser')
        source = page.find('script',attrs={'type':'text/javascript' , 'language':'javascript'})  

        url_pattern = re.compile("/Archives/edgar/data/1277151/000093041312001504/R[0-9]+.htm")
        self.sourcelinks = re.findall(url_pattern,source.text) #TODO:Manually find the pattern of the way the reports are displayed
        
        
        

    
        

    def read(self,*keywords,occurance=10):
        '''
        It works for now just parse through it better and actually use both params
        /Archives/edgar/data/1277151/000093041312001504/R5.htm'
        '''
        indx = 0
        # doc = rq.get(f'https://sec.gov{self.sourcelinks[4]}',headers=headers)
        print(self.sourcelinks)
        if self.sourcelinks is None:
            raise RuntimeError('No sourcelinks to read through.Call find first')
        while True:
            try:
                doc = rq.get(f'https://www.sec.gov/Archives/edgar/data/1277151/000093041312001504/R5.htm',headers=headers) #'https://sec.gov{self.sourcelinks[0]}'
                colnames = BeautifulSoup()
                if any(keywords) in doc:
                    #Print row that keyword in
                    pass
                else:
                    indx += 1 
                    continue
            except:
                print('Could not find any of the keywords. Try other keywords')
            finally:
                Kpage = BeautifulSoup(doc.text, 'html.parser')
                XML = Kpage.find('table') #class report
                rows = XML.find_all('tr',class_=True)
                column_names = XML.find('tr',class_=False).find_all('th')
                nameData= {i.text: []  for i in column_names} #check each row .find('td')[column_names.index(i)]
                # for i in column_names:
                #     nameData[i.text].append(i.find('td')[column_names.index(i)]) #
                for row in rows:
                    #add the td to the key of respective column
                    print(row.text)
                    return row.text
                # print(nameData)
                break
                # for row in rows:
                #     if any(keywords) in row.text:
                #             #print row
                #             print(row.text)   
                #             # sentences = row.text().split('.' and ';')
                #             yield row.text
                
       

    def __str__(self): 
        return f'{self.name}.Keywords:'
 

def getTable():
    """"It works.This need to be more optimize to read it
    Delimiter = seperator like commas in a sentence
    r strings are raw strings which ignores escape characters
    Parse further into excelspreadsheet
    Use string= with .find() to maybe
    
    They will eventually have an API soon"""
    page = rq.get('https://www.tradingview.com/markets/stocks-usa/market-movers-active/')
    soup = BeautifulSoup(page.text, 'html.parser')
    table = soup.find('tbody', class_="tv-data-table__tbody")
    info = table.text
    alltd = table.find_all('td')
    for i in alltd:
        print(i.text)


def getBalanceSheetView():
    """Table Of Balance Sheet from TradeView
    Filter a current ratio of 2
    This does not work because the tag the balance sheet does not exist in the developer tools
    Col is a column tag. colgroup is a parent tag of columns"""
    page = rq.get('https://www.tradingview.com/screener/')
    soup = BeautifulSoup(page.text, 'html.parser')
    divs = soup.find_all('div', recursive=True)
    allchilds = []
    for childs in divs:
        allchilds.append(childs)
    desired = soup.find('div', class_=True)
    print(desired.text)


#obligatory skill counter here that has nothing to do with the project

def SkillsCounter():
    '''Seeing what is in demand on StackOverflow. Modify function as you will.'''
    djcount, flacount = 0, 0
    while True:
        try:
            page = int(input('Type what page you want to go'))
            if page == 0:
                URL = 'https://stackoverflow.com/jobs'
            else:
                URL = 'https://stackoverflow.com/jobs' + f'?pg={page}'
            StackPage = rq.get(URL)
            o = BeautifulSoup(StackPage.text, 'html.parser')
            bar = o.find_all('div', class_='ps-relative d-inline-block z-selected grid gs4 fw-wrap')

            for i in bar:
                skills = str(i.text)

                if 'django' in skills:
                    djcount += 1
                if 'flask' in skills:
                    flacount += 1
            print(f'Django:{djcount},'
                  f'Flask:{flacount}')

        except TypeError:
            print('A number')
        finally:
            print('This was a skills Counter')


#TODO:Update so you dont need a file as an intermediate 
def write(subject):
    try:
        with open('ScrapAndSend.txt','w+') as s:
            s.write(subject)
    except:
        RuntimeError('Cannot Write')
 






