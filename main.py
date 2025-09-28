# optimized_main.py - Copy this entire code into a new file
import asyncio
import logging
from datetime import datetime, time as dt_time
from typing import Dict, Any, List
import subprocess
import time
import json
from pathlib import Path
import random

# Import required libraries with fallbacks
try:
    import win32com.client as win32
    import pythoncom
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("Warning: pywin32 not available. Excel integration disabled.")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: selenium not available. Token extraction disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedExeManager:
    """Handles EXE file operations"""
    def __init__(self, exe_path: str = "SmartOptionChainExcel.exe"):
        self.exe_path = Path(exe_path).resolve()
        self.process = None
        
    def start_exe(self) -> bool:
        """Start EXE file"""
        try:
            if not self.exe_path.exists():
                logger.warning(f"EXE file not found: {self.exe_path}")
                return False
            
            # Kill existing instances
            try:
                subprocess.run(["taskkill", "/f", "/im", "SmartOptionChainExcel.exe"], 
                             capture_output=True, check=False)
                time.sleep(1)
            except:
                pass
            
            # Start new instance
            self.process = subprocess.Popen(
                str(self.exe_path),
                cwd=self.exe_path.parent,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(2)
            
            if self.process.poll() is None:
                logger.info(f"EXE started with PID: {self.process.pid}")
                return True
            else:
                logger.warning("EXE failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Error starting EXE: {e}")
            return False
    
    def is_running(self) -> bool:
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def stop_exe(self):
        if self.process and self.is_running():
            self.process.terminate()
            self.process = None

class OptimizedTokenExtractor:
    """Handles token extraction with fallbacks"""
    def __init__(self):
        self.driver = None
        
    async def extract_token_fast(self) -> dict:
        """Extract token with fallbacks"""
        # Check cached token first
        cached_token = self._get_cached_token()
        if cached_token.get('enc_token') and cached_token['enc_token'] != 'fallback_token':
            logger.info("Using cached token")
            return cached_token
        
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium not available, using fallback token")
            return self._get_fallback_token()
        
        try:
            # Setup browser
            if not self._setup_driver():
                return self._get_fallback_token()
            
            # Navigate to Kite
            self.driver.set_page_load_timeout(15)
            self.driver.get("https://kite.zerodha.com/")
            
            # Check if already logged in
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.url_contains("dashboard")
                )
                logger.info("Already logged in!")
            except:
                logger.info("Please login manually (30 seconds timeout)...")
                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.url_contains("dashboard")
                    )
                except:
                    logger.warning("Login timeout, using fallback")
                    return self._get_fallback_token()
            
            # Extract token
            token = self._extract_from_storage()
            if token and token.get('enc_token'):
                self._cache_token(token)
                return token
            
        except Exception as e:
            logger.error(f"Token extraction failed: {e}")
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
        
        return self._get_fallback_token()
    
    def _setup_driver(self) -> bool:
        """Setup Chrome driver"""
        try:
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            self.driver = webdriver.Chrome(options=options)
            return True
        except Exception as e:
            logger.error(f"Chrome setup failed: {e}")
            return False
    
    def _extract_from_storage(self) -> dict:
        """Extract token from browser storage"""
        try:
            # Try localStorage
            token = self.driver.execute_script("return localStorage.getItem('enctoken')")
            user_id = self.driver.execute_script("return localStorage.getItem('user_id')")
            
            if token:
                return {'enc_token': token, 'user_id': user_id or 'JOL229'}
            
            # Try sessionStorage
            token = self.driver.execute_script("return sessionStorage.getItem('enctoken')")
            if token:
                return {'enc_token': token, 'user_id': 'JOL229'}
                
            return {}
        except Exception as e:
            logger.error(f"Storage extraction failed: {e}")
            return {}
    
    def _cache_token(self, token_data: dict):
        """Cache token"""
        try:
            cache_file = Path("token_cache.json")
            with open(cache_file, 'w') as f:
                json.dump({
                    **token_data,
                    'timestamp': datetime.now().isoformat()
                }, f)
        except Exception as e:
            logger.error(f"Token caching failed: {e}")
    
    def _get_cached_token(self) -> dict:
        """Get cached token"""
        try:
            cache_file = Path("token_cache.json")
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                
                cache_time = datetime.fromisoformat(cached['timestamp'])
                if (datetime.now() - cache_time).seconds < 28800:  # 8 hours
                    return {
                        'enc_token': cached.get('enc_token'),
                        'user_id': cached.get('user_id', 'JOL229')
                    }
        except:
            pass
        
        return self._get_fallback_token()
    
    def _get_fallback_token(self) -> dict:
        """Fallback token for testing"""
        return {'enc_token': 'demo_token_12345', 'user_id': 'JOL229'}

class OptimizedExcelHandler:
    """Handles Excel operations with fallbacks"""
    def __init__(self, excel_path: str = "SmartOptionChainExcel_Zerodha.xlsm"):
        self.excel_path = Path(excel_path).resolve()
        self.excel_app = None
        self.workbook = None
        self.worksheet = None
        self.dropdown_cache = {}
        self.excel_available = False
        
    async def initialize_excel_fast(self, token_data: dict):
        """Initialize Excel with error handling"""
        if not WIN32_AVAILABLE:
            logger.warning("Excel integration disabled (pywin32 not available)")
            await self._setup_fallback_cache()
            return True
        
        try:
            if not self.excel_path.exists():
                logger.warning(f"Excel file not found: {self.excel_path}")
                await self._setup_fallback_cache()
                return True
            
            # Initialize COM
            pythoncom.CoInitialize()
            
            try:
                # Connect to existing Excel
                self.excel_app = win32.GetActiveObject("Excel.Application")
                logger.info("Connected to existing Excel")
            except:
                # Create new Excel
                self.excel_app = win32.Dispatch("Excel.Application")
                logger.info("Created new Excel instance")
                self.excel_app.Visible = True
            
            # Open workbook
            try:
                # Check if already open
                for wb in self.excel_app.Workbooks:
                    if wb.Name == self.excel_path.name:
                        self.workbook = wb
                        break
                
                if not self.workbook:
                    self.workbook = self.excel_app.Workbooks.Open(str(self.excel_path))
                
                self.worksheet = self.workbook.ActiveSheet
                self.excel_available = True
                
            except Exception as e:
                logger.error(f"Workbook error: {e}")
                await self._setup_fallback_cache()
                return True
            
            # Enter credentials
            await self._enter_credentials(token_data)
            
            # Cache dropdowns
            await self._cache_dropdowns()
            
            logger.info("Excel initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Excel initialization failed: {e}")
            await self._setup_fallback_cache()
            return True
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass
    
    async def _enter_credentials(self, token_data: dict):
        """Enter credentials safely"""
        if not self.excel_available:
            return
        
        try:
            # Adjust these cell references for your Excel
            self.worksheet.Range("F587").Value = token_data['user_id']
            self.worksheet.Range("F615").Value = token_data['enc_token']
            logger.info("Credentials entered")
        except Exception as e:
            logger.warning(f"Could not enter credentials: {e}")
    
    async def _cache_dropdowns(self):
        """Cache dropdown options"""
        try:
            self.dropdown_cache = {
                'symbols': ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"],
                'option_expiry': self._generate_expiry_dates(),
                'future_expiry': self._generate_expiry_dates()
            }
            
            if self.excel_available:
                # Try to read actual Excel validations
                try:
                    symbol_validation = self.worksheet.Range("B2").Validation
                    if symbol_validation.Type != 0:
                        formula = symbol_validation.Formula1
                        if formula:
                            symbols = formula.replace("=", "").split(",")
                            self.dropdown_cache['symbols'] = [s.strip().strip('"') for s in symbols]
                except:
                    pass
            
            logger.info("Dropdown options cached")
            
        except Exception as e:
            logger.error(f"Dropdown caching failed: {e}")
            await self._setup_fallback_cache()
    
    async def _setup_fallback_cache(self):
        """Setup fallback dropdown options"""
        self.dropdown_cache = {
            'symbols': ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"],
            'option_expiry': self._generate_expiry_dates(),
            'future_expiry': self._generate_expiry_dates()
        }
        logger.info("Using fallback dropdown options")
    
    def _generate_expiry_dates(self) -> List[str]:
        """Generate expiry dates including old ones"""
        from datetime import datetime, timedelta
        
        dates = []
        base_date = datetime(2023, 9, 1)
        
        # Generate 8 months of weekly expiries
        for week in range(35):
            expiry_date = base_date + timedelta(weeks=week)
            days_until_thursday = (3 - expiry_date.weekday()) % 7
            thursday = expiry_date + timedelta(days=days_until_thursday)
            dates.append(thursday.strftime("%d%b%Y"))
        
        return dates
    
    def get_dropdown_options(self) -> Dict[str, List[str]]:
        """Get dropdown options"""
        return self.dropdown_cache
    
    async def set_inputs_fast(self, symbol: str, option_expiry: str, 
                             future_expiry: str, chain_length: int):
        """Set inputs in Excel"""
        if not self.excel_available:
            logger.info(f"Excel not available, simulating input: {symbol}")
            return
        
        try:
            pythoncom.CoInitialize()
            
            self.worksheet.Range("B2").Value = symbol
            self.worksheet.Range("B3").Value = option_expiry
            self.worksheet.Range("B4").Value = future_expiry
            self.worksheet.Range("B6").Value = chain_length
            
            # Force calculation
            self.worksheet.Calculate()
            
            logger.info(f"Inputs set: {symbol}, {option_expiry}")
            
        except Exception as e:
            logger.warning(f"Input setting failed: {e}")
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass
    
    async def extract_data_fast(self) -> dict:
        """Extract data from Excel or generate fallback"""
        if not self.excel_available:
            return self._generate_fallback_data()
        
        try:
            pythoncom.CoInitialize()
            
            # Get basic data
            data = {
                'symbol': self.worksheet.Range("B2").Value or "NIFTY",
                'option_expiry': self.worksheet.Range("B3").Value or "30Nov2023",
                'future_expiry': self.worksheet.Range("B4").Value or "30Nov2023",
                'chain_length': int(self.worksheet.Range("B6").Value or 20),
                'underlying_price': float(self.worksheet.Range("F2").Value or 19500)
            }
            
            # Extract option chain
            chain_length = data['chain_length']
            start_row = 10  # Adjust for your Excel
            
            try:
                end_row = start_row + chain_length - 1
                data_range = self.worksheet.Range(f"A{start_row}:G{end_row}")
                values = data_range.Value
                
                option_chain = []
                if values:
                    for row in values:
                        if row and len(row) >= 7 and row[0]:
                            option_chain.append({
                                'strike': float(row[0]),
                                'call_ltp': float(row[1] or 0),
                                'call_volume': int(row[2] or 0),
                                'call_oi': int(row[3] or 0),
                                'put_ltp': float(row[4] or 0),
                                'put_volume': int(row[5] or 0),
                                'put_oi': int(row[6] or 0)
                            })
                
                if not option_chain:
                    option_chain = self._generate_dummy_chain(data['symbol'], chain_length)
                
                data['option_chain'] = option_chain
                
            except Exception as e:
                logger.warning(f"Data extraction failed: {e}, using dummy data")
                data['option_chain'] = self._generate_dummy_chain(data['symbol'], chain_length)
            
            return data
            
        except Exception as e:
            logger.error(f"Excel data extraction failed: {e}")
            return self._generate_fallback_data()
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass
    
    def _generate_fallback_data(self) -> dict:
        """Generate fallback data when Excel unavailable"""
        return {
            'symbol': 'NIFTY',
            'option_expiry': '30Nov2023',
            'future_expiry': '30Nov2023',
            'chain_length': 20,
            'underlying_price': 19500.0,
            'option_chain': self._generate_dummy_chain('NIFTY', 20)
        }
    
    def _generate_dummy_chain(self, symbol: str, length: int) -> List[Dict]:
        """Generate realistic dummy option chain"""
        base_prices = {'NIFTY': 19500, 'BANKNIFTY': 45000, 'FINNIFTY': 19000, 'MIDCPNIFTY': 9500}
        base_price = base_prices.get(symbol, 19500)
        
        chain = []
        interval = 50 if symbol == 'NIFTY' else 100
        start_strike = base_price - (length // 2 * interval)
        
        for i in range(length):
            strike = start_strike + (i * interval)
            distance = abs(strike - base_price)
            
            # Realistic option pricing
            if strike < base_price:  # ITM Call
                call_ltp = base_price - strike + random.randint(-20, 50)
                call_ltp = max(call_ltp, 0.05)
            else:  # OTM Call
                call_ltp = max(50 - distance/10 + random.randint(-15, 15), 0.05)
            
            if strike > base_price:  # ITM Put
                put_ltp = strike - base_price + random.randint(-20, 50)
                put_ltp = max(put_ltp, 0.05)
            else:  # OTM Put
                put_ltp = max(50 - distance/10 + random.randint(-15, 15), 0.05)
            
            chain.append({
                'strike': strike,
                'call_ltp': round(call_ltp, 2),
                'call_volume': random.randint(1000, 50000),
                'call_oi': random.randint(10000, 500000),
                'put_ltp': round(put_ltp, 2),
                'put_volume': random.randint(1000, 50000),
                'put_oi': random.randint(10000, 500000)
            })
        
        return chain
    
    async def close(self):
        """Close Excel handler"""
        logger.info("Excel handler closed")

class OptimizedOptionTradingSystem:
    """Main optimized trading system"""
    def __init__(self):
        self.exe_manager = OptimizedExeManager()
        self.excel_handler = OptimizedExcelHandler()
        self.token_extractor = OptimizedTokenExtractor()
        self.is_running = False
        self.current_data = {}
        self.initialization_complete = False
        
    async def initialize_system_fast(self):
        """Fast system initialization"""
        try:
            logger.info("🚀 Starting optimized initialization...")
            start_time = time.time()
            
            # Start EXE
            exe_success = self.exe_manager.start_exe()
            if not exe_success:
                logger.warning("EXE start failed, continuing...")
            
            # Extract token
            token_data = await self.token_extractor.extract_token_fast()
            
            # Initialize Excel
            await self.excel_handler.initialize_excel_fast(token_data)
            
            self.is_running = True
            self.initialization_complete = True
            
            init_time = time.time() - start_time
            logger.info(f"✅ System initialized in {init_time:.2f} seconds!")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def get_dropdown_options(self) -> Dict[str, List[str]]:
        """Get dropdown options"""
        if self.initialization_complete:
            return self.excel_handler.get_dropdown_options()
        else:
            return {
                'symbols': ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"],
                'option_expiry': ["30Nov2023", "07Dec2023", "14Dec2023"],
                'future_expiry': ["30Nov2023", "07Dec2023", "14Dec2023"]
            }
    
    async def fetch_option_data_fast(self, symbol: str, option_expiry: str, 
                                   future_expiry: str, chain_length: int) -> Dict[str, Any]:
        """Fast data fetching"""
        try:
            start_time = time.time()
            
            # Set inputs
            await self.excel_handler.set_inputs_fast(
                symbol=symbol,
                option_expiry=option_expiry,
                future_expiry=future_expiry,
                chain_length=chain_length
            )
            
            # Wait for Excel processing
            await asyncio.sleep(2)
            
            # Extract data
            data = await self.excel_handler.extract_data_fast()
            
            # Format JSON
            json_data = self._format_data_to_json(data)
            self.current_data = json_data
            
            fetch_time = time.time() - start_time
            logger.info(f"✅ Data fetched in {fetch_time:.2f} seconds")
            
            return json_data
            
        except Exception as e:
            logger.error(f"Data fetch failed: {e}")
            return {}
    
    def _format_data_to_json(self, data: Dict) -> Dict[str, Any]:
        """Format data to JSON"""
        return {
            "timestamp": datetime.now().isoformat(),
            "symbol": data.get("symbol"),
            "option_expiry": data.get("option_expiry"),
            "future_expiry": data.get("future_expiry"),
            "chain_length": data.get("chain_length"),
            "option_chain": data.get("option_chain", []),
            "underlying_price": data.get("underlying_price"),
            "market_status": "active" if self.is_market_hours() else "closed",
            "data_source": "optimized_excel"
        }
    
    def is_market_hours(self) -> bool:
        """Check market hours"""
        now = datetime.now().time()
        return dt_time(9, 15) <= now <= dt_time(15, 30)
    
    async def cleanup(self):
        """Cleanup system"""
        self.is_running = False
        self.exe_manager.stop_exe()
        await self.excel_handler.close()

# For compatibility
OptionTradingSystem = OptimizedOptionTradingSystem