# api/fastapi_server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio

app = FastAPI(title="Option Trading API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to hold the trading system instance
trading_system = None

class TradingRequest(BaseModel):
    symbol: str
    option_expiry: str
    future_expiry: str
    chain_length: int

@app.on_event("startup")
async def startup_event():
    """Initialize trading system on startup"""
    global trading_system
    from main import OptionTradingSystem
    trading_system = OptionTradingSystem()

@app.get("/")
async def root():
    return {"message": "Option Trading System API", "status": "running"}

@app.post("/initialize")
async def initialize_system():
    """Initialize the trading system"""
    global trading_system
    try:
        if not trading_system:
            return {"error": "Trading system not available"}
        
        success = await trading_system.initialize_system()
        if success:
            return {"message": "System initialized successfully", "status": "ready"}
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize system")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fetch-data")
async def fetch_option_data(request: TradingRequest):
    """Fetch option chain data"""
    global trading_system
    try:
        if not trading_system or not trading_system.is_running:
            raise HTTPException(status_code=400, detail="System not initialized")
        
        data = await trading_system.fetch_option_data(
            symbol=request.symbol,
            option_expiry=request.option_expiry,
            future_expiry=request.future_expiry,
            chain_length=request.chain_length
        )
        
        if data:
            return {"status": "success", "data": data}
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch data")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get system status"""
    global trading_system
    return {
        "system_initialized": trading_system.is_running if trading_system else False,
        "exe_running": trading_system.exe_manager.is_running() if trading_system else False,
        "market_hours": trading_system.is_market_hours() if trading_system else False
    }

def start_api_server():
    """Start the FastAPI server"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_api_server()