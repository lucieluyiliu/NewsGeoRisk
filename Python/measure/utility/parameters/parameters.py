from datetime import datetime, timedelta
import random
import pandas as pd
import numpy as np


class FilterA:
    def __init__(self):
        self.urgency = 1  # filter for avoiding alert messages (=1 means alert message)
        self.subject = "N2:LEN"  # subject filter represents language in English
        self.language = "en"  # language filter double check English


# For FilterTime, first specify time range yr-mth, then construct list used for looping, change params for diff range
# The Class will automatically construct a list of file names based on start and ending times (for reuters data)
# Note for Reuters data the current max range is from 1996-01 to 2023-09
class FilterTime:
    def __init__(self):
        self.time_start_yr = 1996
        self.time_start_mth = 1
        self.time_end_yr = 2023
        self.time_end_mth = 9

    def generate_time_list(self):
        start_date = datetime(self.time_start_yr, self.time_start_mth, 1)
        end_date = datetime(self.time_end_yr, self.time_end_mth, 1)

        current_date = start_date
        formatted_list = []

        while current_date <= end_date:
            # Format current_date as required string format
            formatted_date = current_date.strftime("%Y-%m")
            formatted_string = f"//research-cifs.unimelb.edu.au/3330-refinitiv/STORY.RTRS.{formatted_date}.REC.JSON.txt.gz"
            formatted_list.append(formatted_string)

            # Increment month
            month = current_date.month + 1
            year = current_date.year
            if month > 12:  # Roll over to next year
                month = 1
                year += 1
            current_date = datetime(year, month, 1)

        return formatted_list


# from the specified range, draw a random file path
# Note for Reuters data the current max range is from 1996-01 to 2023-09
class SingleRandomDrawer:
    def __init__(self):
        self.time_start_yr = 1996
        self.time_start_mth = 1
        self.time_end_yr = 2023
        self.time_end_mth = 9

    def generate_rnd_file(self):
        # Random year generation
        random_year = random.randint(self.time_start_yr, self.time_end_yr)

        # Adjusting the month generation logic based on the selected year
        if random_year == self.time_start_yr:
            random_month = random.randint(self.time_start_mth, 12)
        elif random_year == self.time_end_yr:
            random_month = random.randint(1, self.time_end_mth)
        else:
            random_month = random.randint(1, 12)

        # Creating a datetime object with the random year and month
        random_yr_mth = datetime(random_year, random_month, 1)
        formatted_date = random_yr_mth.strftime("%Y-%m")

        # Constructing the file path
        random_path = f"//research-cifs.unimelb.edu.au/3330-refinitiv/STORY.RTRS." + formatted_date + ".REC.JSON.txt.gz"
        return random_path


# keep  "M:1RT", 'TOPNWS', "M:MR", 'TOPCMB'
class TopNewsList:
    def __init__(self):
        self.TopNewsList = ["M:3Z", "TOPNP","N2:TOP"]

class HeadlineFilterList:
    def __init__(self):
        self.HeadlineFilterList = ["FX Markets Open", "Political and General News Events", "General News Events",'經濟指標','政經日程'
                                   ,'中國報摘','股價對比表','收盘报道','收盤報道','GLANCE','DIARY -','Diary -','World News Highlights','匯市','匯率焦點',
                                   'SUBJECT CODE DIRECTORY', 'Asian News Highlights', 'PRESS DIGEST',
                                   'News Highlights', 'crude swaps and cash trades', 'Air Cargo', 'nan', '新聞摘要',
                                   'CBOT', '恆生指數','ADR股價',
                                   '報摘', '报摘', '香港股市', '報紙新聞摘要', '亞洲股市', 'A股', '新股',
                                   '重要新聞快速瀏覽', '经济指标', '政经日程', '股价', '一览表', '油市',
                                   '中国股市', '全球主要央行动态', '日本数据', '股價表現表', '經濟事件', '主要央行動態',
                                   '一周经济焦点', '加拿大股市', '中国数据',
                                   '外幣期貨', '東京股市', '東南亞股市', '歐洲美元', '紐約美元', '商品貿易數據', '金盤',
                                   '收盤', '開盤', '早盤', '晚盤', 'B股', '重要行事曆',
                                   '海關統計', '東京美元', '盤初', '尾盤', '中國金屬', '匯率預測', '上海國債',
                                   '重要行曆', '黃金焦點', '道瓊工業指數', '金屬期市', '上市報價一覽', 'Nasdaq指數',
                                   '金融市場假期代碼一覽', '滬綜指', '台灣股市','SERVICE ALERT','PRESS DIGEST','TABLE','FX Outlook','Morning Call','closing prices',
                                   'Trading Summary','POLL','key economic indicators','Oil Brief','GUIDE TO REUTERS','TRADING SUMMARY', 'FOREX',
                                   'Morning News Call','DIARY']


class ChinaAmericaList:
    def __init__(self):
        self.ChinaAmericaList = [['China','Chinese'],['U.S.', 'America', 'American','United States','Pentagon']]

# class MasterClass:
#     def __init__(self):
#         self.ChinaAmericaList = ChinaAmericaList()
#

class ChinaAmericaListCN:
    def __init__(self):
        self.ChinaAmericaListCN = [['中国','中方','北京'],['美国', '美方', '华盛顿','美国总统','美利坚合众国','五角大楼']]
        self.ChinaAmericaListCompound = ['中美']
        self.ChinaAmericaListCNTranditional = [['中國', '中方', '北京'], ['美國', '美方', '華盛頓', '美國總統', '美利堅合眾國','五角大樓']]



class CountryDistrictList:
    def __init__(self):
        self.CountryDistrictList = countries_adj_nouns = [
    ['Afghanistan', 'Afghan'],
    ['Albania', 'A12lbanian'],
    ['Algeria', 'Algerian'],
    ['Andorra', 'Andorran'],
    ['Angola', 'Angolan'],
    ['Antigua and Barbuda', 'Antiguan', 'Barbudan'],
    ['Argentina', 'Argentine', 'Argentinian'],
    ['Armenia', 'Armenian'],
    ['Australia', 'Australian'],
    ['Austria', 'Austrian'],
    ['Azerbaijan', 'Azerbaijani'],
    ['Bahamas', 'Bahamian'],
    ['Bahrain', 'Bahraini'],
    ['Bangladesh', 'Bangladeshi'],
    ['Barbados', 'Barbadian'],
    ['Belarus', 'Belarusian'],
    ['Belgium', 'Belgian'],
    ['Belize', 'Belizean'],
    ['Benin', 'Beninese'],
    ['Bhutan', 'Bhutanese'],
    ['Bolivia', 'Bolivian'],
    ['Bosnia and Herzegovina', 'Bosnian', 'Herzegovinian'],
    ['Botswana', 'Botswanan'],
    ['Brazil', 'Brazilian'],
    ['Brunei', 'Bruneian'],
    ['Bulgaria', 'Bulgarian'],
    ['Burkina Faso', 'Burkinabe'],
    ['Burundi', 'Burundian'],
    ['Cabo Verde', 'Cape Verdean'],
    ['Cambodia', 'Cambodian'],
    ['Cameroon', 'Cameroonian'],
    ['Canada', 'Canadian'],
    ['Central African Republic', 'Central African'],
    ['Chad', 'Chadian'],
    ['Chile', 'Chilean'],
    ['China', 'Chinese'],
    ['Hong Kong', 'Hongkongese'],
    ['Taiwan', 'Taiwanese'],
    ['Colombia', 'Colombian'],
    ['Comoros', 'Comorian'],
    ['Congo, Democratic Republic of the', 'Congolese'],
    ['Congo, Republic of the', 'Congolese'],
    ['Costa Rica', 'Costa Rican'],
    ['Cote d\'Ivoire', 'Ivorian'],
    ['Croatia', 'Croatian'],
    ['Cuba', 'Cuban'],
    ['Cyprus', 'Cypriot'],
    ['Czech Republic', 'Czech'],
    ['Denmark', 'Danish'],
    ['Djibouti', 'Djiboutian'],
    ['Dominica', 'Dominican'],
    ['Dominican Republic', 'Dominican'],
    ['Ecuador', 'Ecuadorian'],
    ['Egypt', 'Egyptian'],
    ['El Salvador', 'Salvadoran'],
    ['Equatorial Guinea', 'Equatoguinean'],
    ['Eritrea', 'Eritrean'],
    ['Estonia', 'Estonian'],
    ['Eswatini', 'Swazi'],
    ['Ethiopia', 'Ethiopian'],
    ['Fiji', 'Fijian'],
    ['Finland', 'Finnish'],
    ['France', 'French'],
    ['Gabon', 'Gabonese'],
    ['Gambia', 'Gambian'],
    ['Georgia', 'Georgian'],
    ['Germany', 'German'],
    ['Ghana', 'Ghanaian'],
    ['Greece', 'Greek'],
    ['Grenada', 'Grenadian'],
    ['Guatemala', 'Guatemalan'],
    ['Guinea', 'Guinean'],
    ['Guinea-Bissau', 'Bissau-Guinean'],
    ['Guyana', 'Guyanese'],
    ['Haiti', 'Haitian'],
    ['Honduras', 'Honduran'],
    ['Hungary', 'Hungarian'],
    ['Iceland', 'Icelandic'],
    ['India', 'Indian'],
    ['Indonesia', 'Indonesian'],
    ['Iran', 'Iranian'],
    ['Iraq', 'Iraqi'],
    ['Ireland', 'Irish'],
    ['Israel', 'Israeli'],
    ['Italy', 'Italian'],
    ['Jamaica', 'Jamaican'],
    ['Japan', 'Japanese'],
    ['Jordan', 'Jordanian'],
    ['Kazakhstan', 'Kazakhstani'],
    ['Kenya', 'Kenyan'],
    ['Kiribati', 'I-Kiribati'],
    ['North Korea', 'North Korean'],
    ['South Korea', 'South Korean'],
    ['Kosovo', 'Kosovar'],
    ['Kuwait', 'Kuwaiti'],
    ['Kyrgyzstan', 'Kyrgyz'],
    ['Laos', 'Laotian'],
    ['Latvia', 'Latvian'],
    ['Lebanon', 'Lebanese'],
    ['Lesotho', 'Basotho'],
    ['Liberia', 'Liberian'],
    ['Libya', 'Libyan'],
    ['Liechtenstein', 'Liechtensteiner'],
    ['Lithuania', 'Lithuanian'],
    ['Luxembourg', 'Luxembourgish'],
    ['Madagascar', 'Malagasy'],
    ['Malawi', 'Malawian'],
    ['Malaysia', 'Malaysian'],
    ['Maldives', 'Maldivian'],
    ['Mali', 'Malian'],
    ['Malta', 'Maltese'],
    ['Marshall Islands', 'Marshallese'],
    ['Mauritania', 'Mauritanian'],
    ['Mauritius', 'Mauritian'],
    ['Mexico', 'Mexican'],
    ['Micronesia', 'Micronesian'],
    ['Moldova', 'Moldovan'],
    ['Monaco', 'Monegasque'],
    ['Mongolia', 'Mongolian'],
    ['Montenegro', 'Montenegrin'],
    ['Morocco', 'Moroccan'],
    ['Mozambique', 'Mozambican'],
    ['Myanmar (Burma)', 'Burmese'],
    ['Namibia', 'Namibian'],
    ['Nauru', 'Nauruan'],
    ['Nepal', 'Nepalese'],
    ['Netherlands', 'Dutch'],
    ['New Zealand', 'New Zealander', 'Kiwi'],
    ['Nicaragua', 'Nicaraguan'],
    ['Niger', 'Nigerien'],
    ['Nigeria', 'Nigerian'],
    ['North Macedonia', 'Macedonian'],
    ['Norway', 'Norwegian'],
    ['Oman', 'Omani'],
    ['Pakistan', 'Pakistani'],
    ['Palau', 'Palauan'],
    ['Palestine', 'Palestinian'],
    ['Panama', 'Panamanian'],
    ['Papua New Guinea', 'Papua New Guinean'],
    ['Paraguay', 'Paraguayan'],
    ['Peru', 'Peruvian'],
    ['Philippines', 'Filipino', 'Philippine'],
    ['Poland', 'Polish'],
    ['Portugal', 'Portuguese'],
    ['Qatar', 'Qatari'],
    ['Romania', 'Romanian'],
    ['Russia', 'Russian'],
    ['Rwanda', 'Rwandan'],
    ['Samoa', 'Samoan'],
    ['San Marino', 'Sammarinese'],
    ['Sao Tome and Principe', 'Sao Tomean'],
    ['Saudi Arabia', 'Saudi', 'Saudi Arabian'],
    ['Senegal', 'Senegalese'],
    ['Serbia', 'Serbian'],
    ['Seychelles', 'Seychellois'],
    ['Sierra Leone', 'Sierra Leonean'],
    ['Singapore', 'Singaporean'],
    ['Slovakia', 'Slovak'],
    ['Slovenia', 'Slovenian'],
    ['Solomon Islands', 'Solomon Islander'],
    ['Somalia', 'Somali'],
    ['South Africa', 'South African'],
    ['South Sudan', 'South Sudanese'],
    ['Spain', 'Spanish'],
    ['Sri Lanka', 'Sri Lankan'],
    ['Sudan', 'Sudanese'],
    ['Suriname', 'Surinamese'],
    ['Sweden', 'Swedish'],
    ['Switzerland', 'Swiss'],
    ['Syria', 'Syrian'],
    ['Tajikistan', 'Tajik'],
    ['Tanzania', 'Tanzanian'],
    ['Thailand', 'Thai'],
    ['Timor-Leste', 'East Timorese'],
    ['Togo', 'Togolese'],
    ['Tonga', 'Tongan'],
    ['Trinidad and Tobago', 'Trinidadian', 'Tobagonian'],
    ['Tunisia', 'Tunisian'],
    ['Turkey', 'Turkish'],
    ['Turkmenistan', 'Turkmen'],
    ['Tuvalu', 'Tuvaluan'],
    ['Uganda', 'Ugandan'],
    ['Ukraine', 'Ukrainian'],
    ['United Arab Emirates', 'Emirati', 'UAE'],
    ['United Kingdom', 'British', 'UK'],
    ['United States', 'American', 'America', 'U.S.'],
    ['Uruguay', 'Uruguayan'],
    ['Uzbekistan', 'Uzbek'],
    ['Vanuatu', 'Ni-Vanuatu'],
    ['Vatican City', 'Vatican'],
    ['Venezuela', 'Venezuelan'],
    ['Vietnam', 'Vietnamese'],
    ['Yemen', 'Yemeni'],
    ['Zambia', 'Zambian'],
    ['Zimbabwe', 'Zimbabwean']
]