#ifndef R300_STRUCTURE_MQH
#define R300_STRUCTURE_MQH
#include "R300_Config.mqh"
enum R300StructureBias { STRUCTURE_NEUTRAL = 0, STRUCTURE_BULLISH = 1, STRUCTURE_BEARISH = -1 };
struct R300Swings
  {
   double previousHigh,lastHigh,previousLow,lastLow;
   datetime previousHighTime,highTime,previousLowTime,lowTime;
   int previousHighIndex,highIndex,previousLowIndex,lowIndex;
   double bullishStart,bullishEnd,bearishStart,bearishEnd;
   datetime bullishStartTime,bullishEndTime,bearishStartTime,bearishEndTime;
  };
struct R300StructureState
  {
   R300StructureBias bias;
   bool bosBullish,bosBearish,chochBullish,chochBearish;
   double previousSwingHigh,lastSwingHigh,previousSwingLow,lastSwingLow;
   double protectedHigh,protectedLow;
  };

bool R300_IsSwing(const MqlRates &bars[],const int index,const int strength,const bool high)
  {
   if(index-strength < 0 || index+strength >= ArraySize(bars)) return(false);
   for(int k=1;k<=strength;k++)
     {
      if(high && (bars[index].high <= bars[index-k].high || bars[index].high <= bars[index+k].high)) return(false);
      if(!high && (bars[index].low >= bars[index-k].low || bars[index].low >= bars[index+k].low)) return(false);
     }
   return(true);
  }
void R300_AddSwing(const MqlRates &bars[],const int index,R300Swings &s)
  {
   bool high = R300_IsSwing(bars,index,InpSwingStrength,true);
   bool low = R300_IsSwing(bars,index,InpSwingStrength,false);
   if(high)
     {
      s.previousHigh=s.lastHigh; s.previousHighTime=s.highTime; s.previousHighIndex=s.highIndex;
      s.lastHigh=bars[index].high; s.highTime=bars[index].time; s.highIndex=index;
      if(s.lowTime > 0 && s.lowTime < s.highTime && s.lastLow < s.lastHigh)
        {
         s.bullishStart=s.lastLow; s.bullishEnd=s.lastHigh;
         s.bullishStartTime=s.lowTime; s.bullishEndTime=s.highTime;
        }
     }
   if(low)
     {
      s.previousLow=s.lastLow; s.previousLowTime=s.lowTime; s.previousLowIndex=s.lowIndex;
      s.lastLow=bars[index].low; s.lowTime=bars[index].time; s.lowIndex=index;
      // A candle that is both a high and low cannot imply an intrabar impulse.
      if(s.highTime > 0 && s.highTime < s.lowTime && s.lastHigh > s.lastLow)
        {
         s.bearishStart=s.lastHigh; s.bearishEnd=s.lastLow;
         s.bearishStartTime=s.highTime; s.bearishEndTime=s.lowTime;
        }
     }
  }
void R300_FindSwings(const MqlRates &bars[],R300Swings &s)
  {
   ZeroMemory(s);
   // A pivot needs strength CLOSED right-side candles; no candle 0 is copied.
   for(int i=ArraySize(bars)-InpSwingStrength-1;i>=InpSwingStrength;i--)
      R300_AddSwing(bars,i,s);
  }
R300StructureBias R300_SwingBias(const R300Swings &s)
  {
   if(s.previousHighTime == 0 || s.previousLowTime == 0) return(STRUCTURE_NEUTRAL);
   if(s.lastHigh > s.previousHigh && s.lastLow > s.previousLow) return(STRUCTURE_BULLISH);
   if(s.lastHigh < s.previousHigh && s.lastLow < s.previousLow) return(STRUCTURE_BEARISH);
   return(STRUCTURE_NEUTRAL);
  }
datetime r300StructureBar=0;
R300StructureState r300CachedStructure;
bool R300_EvaluateH1Structure(R300StructureState &state)
  {
   datetime stamp=iTime(_Symbol,PERIOD_H1,1);
   if(stamp == 0) return(false);
   if(stamp != r300StructureBar)
     {
      MqlRates bars[];
      if(!R300_ClosedRates(PERIOD_H1,InpSwingLookback,bars)) return(false);
      R300Swings s; ZeroMemory(s);
      R300StructureState next; ZeroMemory(next);
      // Chronological replay of already-closed history establishes prior bias.
      // At evaluation index i, the newest confirmable pivot is i+strength.
      for(int i=ArraySize(bars)-2*InpSwingStrength-1;i>=0;i--)
        {
         R300StructureBias prior=next.bias;
         double priorHigh=next.protectedHigh, priorLow=next.protectedLow;
         R300_AddSwing(bars,i+InpSwingStrength,s);
         next.bosBullish=(s.highTime > 0 && bars[i+1].close <= s.lastHigh && bars[i].close > s.lastHigh);
         next.bosBearish=(s.lowTime > 0 && bars[i+1].close >= s.lastLow && bars[i].close < s.lastLow);
         next.chochBearish=(prior == STRUCTURE_BULLISH && priorLow > 0 && bars[i+1].close >= priorLow && bars[i].close < priorLow);
         next.chochBullish=(prior == STRUCTURE_BEARISH && priorHigh > 0 && bars[i+1].close <= priorHigh && bars[i].close > priorHigh);
         next.bias=R300_SwingBias(s);
         // Baseline assumption: protected level is the latest confirmed swing
         // from the preceding evaluation, not a future pivot.
         next.protectedHigh=s.lastHigh; next.protectedLow=s.lastLow;
        }
      next.previousSwingHigh=s.previousHigh; next.lastSwingHigh=s.lastHigh;
      next.previousSwingLow=s.previousLow; next.lastSwingLow=s.lastLow;
      r300CachedStructure=next; r300StructureBar=stamp;
     }
   state=r300CachedStructure;
   return(true);
  }
#endif
