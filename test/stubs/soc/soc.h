#pragma once
#define REG_WRITE(reg,value) do { (void)(reg); if ((value) & (1UL<<14)) mockPins[14]=0; } while (0)
