#define TESTDDS 1

	SHUTR    1
	DELAY    us_MeasTime
	SHUTR    0	
	DDSAMP	 TESTDDS, A_DDS1
	DELAY    us_MeasTime
	SHUTR	 1
	END
