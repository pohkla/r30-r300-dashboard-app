#property strict
#property version "1.00"
#property description "R300 EA skeleton. Safe mode only; strategy pending specification."

#include "R300_Config.mqh"
#include "R300_Trend.mqh"
#include "R300_Structure.mqh"
#include "R300_Setup.mqh"
#include "R300_Entry.mqh"
#include "R300_Risk.mqh"
#include "R300_Exit.mqh"

int OnInit()
  {
   Print("R300 EA initialized");
   Print("Trading mode: ", R300_TRADING_MODE);
   Print("Symbol: ", _Symbol);
   Print("Broker: ", AccountInfoString(ACCOUNT_COMPANY));
   Print("Server: ", AccountInfoString(ACCOUNT_SERVER));
   Print("Version: ", R300_VERSION);
   Print("Safe Mode: ", R300_SAFE_MODE ? "ON" : "OFF");
   Print("Magic Number (metadata only): ", InpMagicNumber);
   if(_Symbol != InpExpectedSymbol)
      Print("Notice: expected symbol is ", InpExpectedSymbol,
            "; current chart symbol is ", _Symbol);
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   Print("R300 EA deinitialized. Reason: ", reason);
  }

void OnTick()
  {
   // Intentionally inert. All strategy rules await docs/R300_SPEC.md.
   // No signals, account changes, or position management in this version.
  }
