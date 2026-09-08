#ifndef R300_CONFIG_MQH
#define R300_CONFIG_MQH
#define R300_VERSION "0.10"
const bool R300_SAFE_MODE = true;
const string R300_TRADING_MODE = "SIGNAL ONLY / VIRTUAL BACKTEST SAFE MODE";

input group "Metadata"
input ulong InpMagicNumber = 300;
input string InpExpectedSymbol = "GOLD";
input group "H4 Trend"
input int InpH4FastEMA = 50;
input int InpH4SlowEMA = 200;
input int InpH4SlopeBars = 3;
input group "Confirmed Swings"
input int InpSwingStrength = 2;
input int InpSwingLookback = 512;
input group "M15 Setup"
input int InpRSIPeriod = 14;
input double InpFibMin = 0.50;
input double InpFibMax = 0.786;
input int InpVolumeProfileBars = 120;
input int InpVolumeProfileBins = 48;
input double InpPOCATRDistance = 0.50;
input int InpMinimumSetupScore = 2;
input group "M5 Entry"
input double InpRejectionWickRatio = 2.0;
input double InpRetestATRDistance = 0.20;
input int InpRetestMaxBars = 5;
input group "Virtual Risk"
input int InpATRPeriod = 14;
input double InpSLATRBuffer = 0.20;
input double InpRiskReward = 2.0;
enum R300SimulationMode { R300_TICK_SEQUENCE = 0, R300_CLOSED_BAR_CONSERVATIVE = 1 };
input group "Virtual Test"
input int InpMaxVirtualTradeBars = 288;
input R300SimulationMode InpSimulationMode = R300_TICK_SEQUENCE;
input bool InpDrawSignals = true;

bool R300_ValidInputs()
  {
   return(InpH4FastEMA > 0 && InpH4SlowEMA > InpH4FastEMA &&
          InpH4SlowEMA <= 10000 && InpH4SlopeBars > 0 && InpH4SlopeBars <= 1000 &&
          InpSwingStrength > 0 && InpSwingStrength <= 100 &&
          InpSwingLookback >= 2*InpSwingStrength+5 && InpSwingLookback <= 10000 &&
          InpRSIPeriod > 0 && InpRSIPeriod <= 1000 &&
          InpFibMin >= 0 && InpFibMin < InpFibMax && InpFibMax <= 1 &&
          InpVolumeProfileBars >= 2 && InpVolumeProfileBars <= 10000 &&
          InpVolumeProfileBins >= 2 && InpVolumeProfileBins <= 10000 &&
          MathIsValidNumber(InpPOCATRDistance) && InpPOCATRDistance >= 0 &&
          InpMinimumSetupScore >= 1 && InpMinimumSetupScore <= 3 &&
          MathIsValidNumber(InpRejectionWickRatio) && InpRejectionWickRatio > 0 &&
          MathIsValidNumber(InpRetestATRDistance) && InpRetestATRDistance >= 0 &&
          InpRetestMaxBars > 0 && InpRetestMaxBars <= 10000 &&
          InpATRPeriod > 0 && InpATRPeriod <= 1000 &&
          MathIsValidNumber(InpSLATRBuffer) && InpSLATRBuffer >= 0 &&
          MathIsValidNumber(InpRiskReward) && InpRiskReward > 0 &&
          InpMaxVirtualTradeBars > 0 && InpMaxVirtualTradeBars <= 1000000 &&
          (InpSimulationMode == R300_TICK_SEQUENCE || InpSimulationMode == R300_CLOSED_BAR_CONSERVATIVE));
  }

// Index zero in these arrays is broker shift 1, NEVER the forming candle.
bool R300_ClosedRates(const ENUM_TIMEFRAMES tf,const int count,MqlRates &rates[])
  {
   ArraySetAsSeries(rates,true);
   return(CopyRates(_Symbol,tf,1,count,rates) == count);
  }
bool R300_BufferValue(const int handle,const int shift,double &value)
  {
   if(handle == INVALID_HANDLE || shift < 1) return(false);
   double values[1];
   if(CopyBuffer(handle,0,shift,1,values) != 1) return(false);
   value = values[0];
   return(MathIsValidNumber(value) && value != EMPTY_VALUE);
  }
void R300_ReleaseHandle(int &handle)
  {
   if(handle != INVALID_HANDLE) IndicatorRelease(handle);
   handle = INVALID_HANDLE;
  }
#endif
