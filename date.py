# from datetime import datetime

# days_difference = (datetime.now() - datetime.strptime("2005-04-01", "%Y-%m-%d")).days
# print("Number of days from input date to current date:", days_difference)
import yfinance as yf

def download_stock_data(symbol):# start , end
    # Download historical stock data
    stock_data = yf.download(symbol + ".NS")#, start=start_date, end=end_date
    
    # Save data to CSV file
    stock_data.to_csv(symbol + "_historical_data.csv")

# Example usage
symbol = "BHEL"  # Replace this with the symbol of the stock you want to download
# stock_data = yf.download(symbol + ".NS")
# start_date = stock_data.index.min().date()  # Start date in format "YYYY-MM-DD"
# end_date = stock_data.index.max().date()    # End date in format "YYYY-MM-DD"

download_stock_data(symbol)
