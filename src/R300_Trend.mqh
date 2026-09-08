#ifndef R300_TREND_MQH
#define R300_TREND_MQH
#include "R300_Config.mqh"
enum R300Trend { R300_TREND_NEUTRAL = 0, R300_TREND_BULLISH = 1, R300_TREND_BEARISH = -1 };
int r300FastEMA = INVALID_HANDLE, r300SlowEMA = INVALID_HANDLE;
datetime r300TrendBar = 0;
R300Trend r300CachedTrend = R300_TREND_NEUTRAL;
bool R300_TrendInit()
  {
   r300TrendBar = 0;
   r300FastEMA = iMA(_Symbol,PERIOD_H4,InpH4FastEMA,0,MODE_EMA,PRICE_CLOSE);
   r300SlowEMA = iMA(_Symbol,PERIOD_H4,InpH4SlowEMA,0,MODE_EMA,PRICE_CLOSE);
   return(r300FastEMA != INVALID_HANDLE && r300SlowEMA != INVALID_HANDLE);
  }
void R300_TrendRelease()
  {
   R300_ReleaseHandle(r300FastEMA);
   R300_ReleaseHandle(r300SlowEMA);
  }
bool R300_EvaluateH4Trend(R300Trend &trend)
  {
   datetime stamp = iTime(_Symbol,PERIOD_H4,1);
   if(stamp == 0) return(false);
   if(stamp != r300TrendBar)
     {
      if(BarsCalculated(r300SlowEMA) < InpH4SlowEMA+InpH4SlopeBars+2) return(false);
      double fast,slow,past;
      MqlRates bars[];
      // Current CONFIRMED EMA is shift 1; slope compares shift 1+n.
      if(!R300_ClosedRates(PERIOD_H4,1,bars) ||
         !R300_BufferValue(r300FastEMA,1,fast) ||
         !R300_BufferValue(r300SlowEMA,1,slow) ||
         !R300_BufferValue(r300FastEMA,1+InpH4SlopeBars,past)) return(false);
      r300CachedTrend = R300_TREND_NEUTRAL;
      if(fast > slow && bars[0].close > fast && fast > past) r300CachedTrend = R300_TREND_BULLISH;
      if(fast < slow && bars[0].close < fast && fast < past) r300CachedTrend = R300_TREND_BEARISH;
      r300TrendBar = stamp;
     }
   trend = r300CachedTrend;
   return(true);
  }
#endif
