import streamlit as st
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import pandas as pd
import plotly
import plotly.express as px
import json 
# NLTK VADER for sentiment analysis
import nltk
nltk.downloader.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import cufflinks as cf
import yfinance as yf
from datetime import datetime

st.header("Análise de sentimento - stock news")
st.markdown('Carregando dados atualizados podemos monitorar o comportamento das ações listadas na bolsa americana.')
st.markdown('NLTK é uma biblioteca de linguagem natural que permite fácil implementação e utilização.')
st.markdown('Benjamin Graham, autor do Investidor Inteligente, introduz o "Sr. Mercado" como um persongem muito racional a longo prazo, porém no curto prazo ele tende a ser muito sensível e volátil com divulgação de notícias.')
st.markdown('Com SentimentIntensityAnalyzer foi possível criar uma breve visualização dos sentimentos do "Sr. Mercado no momento.')


def get_news(ticker):
    url = finviz_url + ticker
    req = Request(url=url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'}) 
    response = urlopen(req)    
    # Read the contents of the file into 'html'
    html = BeautifulSoup(response)
    # Find 'news-table' in the Soup and load it into 'news_table'
    news_table = html.find(id='news-table')
    return news_table
	
# parse news into dataframe
def parse_news(news_table):
    parsed_news = []
    
    for x in news_table.findAll('tr'):
        # occasionally x (below) may be None when the html table is poorly formatted, skip it in try except instead of throwing an error and exiting
        # may also use an if loop here to check if x is None first	
        try:
            # read the text from each tr tag into text
            # get text from a only
            text = x.a.get_text() 
            # splite text in the td tag into a list 
            date_scrape = x.td.text.split()
            # if the length of 'date_scrape' is 1, load 'time' as the only element

            if len(date_scrape) == 1:
                time = date_scrape[0]				
			# else load 'date' as the 1st element and 'time' as the second    
            else:
                date = date_scrape[0]
                time = date_scrape[1]
			
            # Append ticker, date, time and headline as a list to the 'parsed_news' list
            parsed_news.append([date, time, text])        
            
            
        except:
            pass
			
    # Set column names
    columns = ['date', 'time', 'headline']
    # Convert the parsed_news list into a DataFrame called 'parsed_and_scored_news'
    parsed_news_df = pd.DataFrame(parsed_news, columns=columns)        
    # Create a pandas datetime object from the strings in 'date' and 'time' column
    parsed_news_df['datetime'] = pd.to_datetime(parsed_news_df['date'] + ' ' + parsed_news_df['time'])
			
    return parsed_news_df
        
    
        
def score_news(parsed_news_df):
    # Instantiate the sentiment intensity analyzer
    vader = SentimentIntensityAnalyzer()
    
    # Iterate through the headlines and get the polarity scores using vader
    scores = parsed_news_df['headline'].apply(vader.polarity_scores).tolist()

    # Convert the 'scores' list of dicts into a DataFrame
    scores_df = pd.DataFrame(scores)

    # Join the DataFrames of the news and the list of dicts
    parsed_and_scored_news = parsed_news_df.join(scores_df, rsuffix='_right')             
    parsed_and_scored_news = parsed_and_scored_news.set_index('datetime')    
    parsed_and_scored_news = parsed_and_scored_news.drop(['date', 'time'], 1)          
    parsed_and_scored_news = parsed_and_scored_news.rename(columns={"compound": "sentiment_score"})

    return parsed_and_scored_news

def plot_hourly_sentiment(parsed_and_scored_news, ticker):
   
    # Group by date and ticker columns from scored_news and calculate the mean
    mean_scores = parsed_and_scored_news.resample('H').mean()

    # Plot a bar chart with plotly
    fig = px.bar(mean_scores, x=mean_scores.index, y='sentiment_score', title = ticker + '- Score de sentiment analysis por hora')
    return fig # instead of using fig.show(), we return fig and turn it into a graphjson object for displaying in web page later

def plot_daily_sentiment(parsed_and_scored_news, ticker):
   
    # Group by date and ticker columns from scored_news and calculate the mean
    mean_scores = parsed_and_scored_news.resample('D').mean()

    # Plot a bar chart with plotly
    fig = px.bar(mean_scores, x=mean_scores.index, y='sentiment_score', title = ticker + '- Score de sentiment analysis diário')
    return fig # instead of using fig.show(), we return fig and turn it into a graphjson object for displaying in web page later

# for extracting data from finviz
finviz_url = 'https://finviz.com/quote.ashx?t='


ticker = st.text_input('Escolha o código do ativo.', '').upper()

df = pd.DataFrame({'datetime': datetime.now(), 'ticker': ticker}, index = [0])



try:
	st.subheader("Sentimentos do ativo {} ".format(ticker))
	
except Exception as e:
	print(str(e))
	st.write("Insira um código válido, exemplo: 'AAPL' e pressione Enter.")	



try:
    #Gráfico horário
    news_table = get_news(ticker)
    parsed_news_df = parse_news(news_table)
    print(parsed_news_df)
    parsed_and_scored_news = score_news(parsed_news_df)
    fig_hourly = plot_hourly_sentiment(parsed_and_scored_news, ticker)
    fig_daily = plot_daily_sentiment(parsed_and_scored_news, ticker) 
       
    st.plotly_chart(fig_hourly)

        
except Exception as e:
    print(str(e))
    st.write("")	


try:
    #Bollinger Bands
    import datetime
    start_date =  datetime.date(2022, 1, 1)
    end_date = datetime.date(2022, 9, 24)
    tickerSymbol =ticker
    tickerData = yf.Ticker(tickerSymbol) # Get ticker data
    tickerDf = tickerData.history(period='1d', start=start_date, end=end_date)
    qf=cf.QuantFig(tickerDf,title='Bollinger Bands',legend='top',name='GS')
    qf.add_bollinger_bands()
    fig = qf.iplot(asFigure=True)
    st.plotly_chart(fig)

except Exception as e:
    print(str(e))
    st.error("YahooFinance pode estar com problemas para buscar os dados.", icon="🚨")

### Table news, hourly chart, stock description
try:
	st.subheader("")
	news_table = get_news(ticker)
	parsed_news_df = parse_news(news_table)
	print(parsed_news_df)
	parsed_and_scored_news = score_news(parsed_news_df)
	fig_hourly = plot_hourly_sentiment(parsed_and_scored_news, ticker)
	fig_daily = plot_daily_sentiment(parsed_and_scored_news, ticker) 
	 
	st.plotly_chart(fig_daily)

	description = """
		A tabela abaixo trás cada tema mais recente sobre o ativo e um status negative, neutral, positive e trás um score "sentimental".
		Os temas das notícias são do website FinViz.
		Os sentimentos são avaliados pelo nltk.sentiment.vader, uma biblioteca Python.
		""".format(ticker)
		
	st.write(description)	 
	st.table(parsed_and_scored_news)
	
except Exception as e:
	print(str(e))
	st.write("")	




hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
