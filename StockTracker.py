import requests
import pandas as pd
import datetime
import json
import os
import matplotlib.pyplot as plt
from tabulate import tabulate
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class StockPortfolioTracker:
    def __init__(self, api_key=None):
        # Add error handling for API key
        self.api_key = api_key or os.environ.get('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            print("Warning: No API key provided. Using demo mode.")
            self.api_key = 'demo'
        self.portfolio_file = 'portfolio.json'
        self.portfolio = self._load_portfolio()
        
    def _load_portfolio(self):
        """Load portfolio from file if exists, otherwise return empty dict"""
        if os.path.exists(self.portfolio_file):
            with open(self.portfolio_file, 'r') as f:
                return json.load(f)
        return {"stocks": [], "transactions": [], "cash": 0}
    
    def _save_portfolio(self):
        """Save portfolio to file"""
        with open(self.portfolio_file, 'w') as f:
            json.dump(self.portfolio, f, indent=4)
    
    def get_stock_price(self, symbol):
        """Get current stock price using Alpha Vantage API"""
        try:
            url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.api_key}'
            response = requests.get(url)
            data = response.json()
            
            if 'Error Message' in data:
                print(f"Error: {data['Error Message']}")
                return None
            
            if 'Global Quote' in data and data['Global Quote']:
                return float(data['Global Quote']['05. price'])
            else:
                print(f"Error: No data found for symbol {symbol}")
                return None
                
        except Exception as e:
            print(f"Error fetching stock data: {e}")
            # For demo, return a mock price if API fails
            import random
            return round(random.uniform(50, 500), 2)
    
    def add_cash(self, amount):
        """Add cash to portfolio"""
        self.portfolio["cash"] += amount
        
        # Add transaction
        transaction = {
            "type": "cash_deposit",
            "amount": amount,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.portfolio["transactions"].append(transaction)
        
        self._save_portfolio()
        print(f"Added ${amount:.2f} to portfolio. New cash balance: ${self.portfolio['cash']:.2f}")
    
    def withdraw_cash(self, amount):
        """Withdraw cash from portfolio"""
        if amount > self.portfolio["cash"]:
            print(f"Error: Insufficient funds. Current cash balance: ${self.portfolio['cash']:.2f}")
            return False
            
        self.portfolio["cash"] -= amount
        
        # Add transaction
        transaction = {
            "type": "cash_withdrawal",
            "amount": amount,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.portfolio["transactions"].append(transaction)
        
        self._save_portfolio()
        print(f"Withdrew ${amount:.2f} from portfolio. New cash balance: ${self.portfolio['cash']:.2f}")
        return True
    
    def buy_stock(self, symbol, shares, price=None):
        """Buy shares of a stock"""
        # Get current price if not provided
        if price is None:
            price = self.get_stock_price(symbol)
            if price is None:
                return False
                
        total_cost = price * shares
        
        # Check if enough cash
        if total_cost > self.portfolio["cash"]:
            print(f"Error: Insufficient funds. Need ${total_cost:.2f}, have ${self.portfolio['cash']:.2f}")
            return False
        
        # Update cash balance
        self.portfolio["cash"] -= total_cost
        
        # Check if stock already in portfolio
        existing_stock = None
        for stock in self.portfolio["stocks"]:
            if stock["symbol"] == symbol:
                existing_stock = stock
                break
                
        if existing_stock:
            # Update existing position
            total_shares = existing_stock["shares"] + shares
            total_cost = (existing_stock["shares"] * existing_stock["avg_price"]) + (shares * price)
            existing_stock["avg_price"] = total_cost / total_shares
            existing_stock["shares"] = total_shares
        else:
            # Add new position
            self.portfolio["stocks"].append({
                "symbol": symbol,
                "shares": shares,
                "avg_price": price,
                "purchase_date": datetime.datetime.now().strftime("%Y-%m-%d")
            })
        
        # Add transaction
        transaction = {
            "type": "buy",
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "total": total_cost,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.portfolio["transactions"].append(transaction)
        
        self._save_portfolio()
        print(f"Bought {shares} shares of {symbol} at ${price:.2f} for a total of ${total_cost:.2f}")
        return True
    
    def sell_stock(self, symbol, shares, price=None):
        """Sell shares of a stock"""
        # Find the stock in portfolio
        stock_index = None
        for i, stock in enumerate(self.portfolio["stocks"]):
            if stock["symbol"] == symbol:
                stock_index = i
                break
                
        if stock_index is None:
            print(f"Error: {symbol} not found in portfolio")
            return False
            
        stock = self.portfolio["stocks"][stock_index]
        
        # Check if enough shares
        if shares > stock["shares"]:
            print(f"Error: Insufficient shares. Have {stock['shares']}, trying to sell {shares}")
            return False
            
        # Get current price if not provided
        if price is None:
            price = self.get_stock_price(symbol)
            if price is None:
                return False
                
        total_proceeds = price * shares
        
        # Update cash balance
        self.portfolio["cash"] += total_proceeds
        
        # Update stock position
        if shares == stock["shares"]:
            # Remove stock if selling all shares
            self.portfolio["stocks"].pop(stock_index)
        else:
            # Update shares count
            stock["shares"] -= shares
            
        # Add transaction
        transaction = {
            "type": "sell",
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "total": total_proceeds,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.portfolio["transactions"].append(transaction)
        
        self._save_portfolio()
        print(f"Sold {shares} shares of {symbol} at ${price:.2f} for a total of ${total_proceeds:.2f}")
        return True
    
    def show_portfolio(self):
        """Display the current portfolio with performance metrics"""
        if not self.portfolio["stocks"]:
            print("Portfolio is empty. Add some stocks to get started!")
            return
            
        # Get current prices and calculate performance
        portfolio_data = []
        total_value = 0
        total_cost = 0
        
        for stock in self.portfolio["stocks"]:
            symbol = stock["symbol"]
            shares = stock["shares"]
            avg_price = stock["avg_price"]
            cost_basis = shares * avg_price
            
            # Get current price
            current_price = self.get_stock_price(symbol)
            current_value = shares * current_price
            
            # Calculate gains/losses
            gain_loss = current_value - cost_basis
            gain_loss_pct = (gain_loss / cost_basis) * 100
            
            portfolio_data.append([
                symbol,
                shares,
                f"${avg_price:.2f}",
                f"${current_price:.2f}",
                f"${cost_basis:.2f}",
                f"${current_value:.2f}",
                f"${gain_loss:.2f}",
                f"{gain_loss_pct:.2f}%"
            ])
            
            total_value += current_value
            total_cost += cost_basis
        
        # Add cash to total value
        total_with_cash = total_value + self.portfolio["cash"]
        
        # Calculate overall performance
        total_gain_loss = total_value - total_cost
        total_gain_loss_pct = (total_gain_loss / total_cost) * 100 if total_cost > 0 else 0
        
        # Print portfolio table
        headers = ["Symbol", "Shares", "Avg Price", "Current Price", "Cost Basis", "Current Value", "Gain/Loss", "Gain/Loss %"]
        print("\n--- STOCK HOLDINGS ---")
        print(tabulate(portfolio_data, headers=headers, tablefmt="grid"))
        
        # Print summary
        print("\n--- PORTFOLIO SUMMARY ---")
        print(f"Total Stock Value: ${total_value:.2f}")
        print(f"Cash Balance: ${self.portfolio['cash']:.2f}")
        print(f"Total Portfolio Value: ${total_with_cash:.2f}")
        print(f"Total Cost Basis: ${total_cost:.2f}")
        print(f"Total Gain/Loss: ${total_gain_loss:.2f} ({total_gain_loss_pct:.2f}%)")
    
    def show_transactions(self, limit=10):
        """Display recent transactions"""
        if not self.portfolio["transactions"]:
            print("No transactions found.")
            return
            
        transactions = sorted(self.portfolio["transactions"], key=lambda x: x["date"], reverse=True)
        
        print(f"\n--- RECENT TRANSACTIONS (Last {min(limit, len(transactions))}) ---")
        
        # Format transaction data
        transaction_data = []
        for t in transactions[:limit]:
            if t["type"] == "buy":
                transaction_data.append([
                    t["date"],
                    "BUY",
                    t["symbol"],
                    t["shares"],
                    f"${t['price']:.2f}",
                    f"${t['total']:.2f}"
                ])
            elif t["type"] == "sell":
                transaction_data.append([
                    t["date"],
                    "SELL",
                    t["symbol"],
                    t["shares"],
                    f"${t['price']:.2f}",
                    f"${t['total']:.2f}"
                ])
            elif t["type"] in ["cash_deposit", "cash_withdrawal"]:
                transaction_data.append([
                    t["date"],
                    "CASH " + t["type"].split("_")[1].upper(),
                    "-",
                    "-",
                    "-",
                    f"${t['amount']:.2f}"
                ])
                
        headers = ["Date", "Type", "Symbol", "Shares", "Price", "Total"]
        print(tabulate(transaction_data, headers=headers, tablefmt="grid"))
    
    def generate_performance_chart(self):
        """Generate a portfolio performance chart"""
        if not self.portfolio["stocks"]:
            print("Portfolio is empty. Add some stocks to generate a chart.")
            return
            
        # Collect data for chart
        labels = []
        values = []
        costs = []
        
        for stock in self.portfolio["stocks"]:
            symbol = stock["symbol"]
            shares = stock["shares"]
            avg_price = stock["avg_price"]
            current_price = self.get_stock_price(symbol)
            
            labels.append(symbol)
            values.append(shares * current_price)
            costs.append(shares * avg_price)
        
        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
        
        # Pie chart showing portfolio allocation
        ax1.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Portfolio Allocation')
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        # Bar chart showing value vs. cost basis
        x = range(len(labels))
        width = 0.35
        
        ax2.bar(x, values, width, label='Current Value')
        ax2.bar([i + width for i in x], costs, width, label='Cost Basis')
        
        ax2.set_xlabel('Stocks')
        ax2.set_ylabel('Value ($)')
        ax2.set_title('Value vs. Cost Basis')
        ax2.set_xticks([i + width/2 for i in x])
        ax2.set_xticklabels(labels)
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig('portfolio_performance.png')
        plt.close()
        
        print("Performance chart saved as 'portfolio_performance.png'")

def main():
    # Check for API key in environment
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("No API key found. Using demo mode with limited functionality.")
        print("For full functionality, obtain an API key from Alpha Vantage and set it as an environment variable:")
        print("export ALPHA_VANTAGE_API_KEY='your_api_key'")
    
    tracker = StockPortfolioTracker(api_key)
    
    while True:
        print("\n=== STOCK PORTFOLIO TRACKER ===")
        print("1. View Portfolio")
        print("2. Buy Stock")
        print("3. Sell Stock")
        print("4. Add Cash")
        print("5. Withdraw Cash")
        print("6. View Transactions")
        print("7. Generate Performance Chart")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ")
        
        if choice == '1':
            tracker.show_portfolio()
            
        elif choice == '2':
            symbol = input("Enter stock symbol: ").upper()
            try:
                shares = float(input("Enter number of shares: "))
                tracker.buy_stock(symbol, shares)
            except ValueError:
                print("Invalid input. Please enter a number for shares.")
                
        elif choice == '3':
            symbol = input("Enter stock symbol: ").upper()
            try:
                shares = float(input("Enter number of shares: "))
                tracker.sell_stock(symbol, shares)
            except ValueError:
                print("Invalid input. Please enter a number for shares.")
                
        elif choice == '4':
            try:
                amount = float(input("Enter amount to deposit: "))
                tracker.add_cash(amount)
            except ValueError:
                print("Invalid input. Please enter a number for amount.")
                
        elif choice == '5':
            try:
                amount = float(input("Enter amount to withdraw: "))
                tracker.withdraw_cash(amount)
            except ValueError:
                print("Invalid input. Please enter a number for amount.")
                
        elif choice == '6':
            tracker.show_transactions()
            
        elif choice == '7':
            tracker.generate_performance_chart()
            
        elif choice == '8':
            print("Exiting program. Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()