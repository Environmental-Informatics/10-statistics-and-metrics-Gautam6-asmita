#!/bin/env python
# Created on March 25, 2020
#  by Keith Cherkauer
#
# This script servesa as the solution set for assignment-10 on descriptive
# statistics and environmental informatics.  See the assignment documention 
# and repository at:
# https://github.com/Environmental-Informatics/assignment-10.git for more
# details about the assignment.
#Completed by : Asmita Gautam
#Assignment completed on: 11th april 2020
#
import pandas as pd
import scipy.stats as stats
import numpy as np

def ReadData( fileName ):
    """This function takes a filename as input, and returns a dataframe with
    raw data read from that file in a Pandas DataFrame.  The DataFrame index
    should be the year, month and day of the observation.  DataFrame headers
    should be "agency_cd", "site_no", "Date", "Discharge", "Quality". The 
    "Date" column should be used as the DataFrame index. The pandas read_csv
    function will automatically replace missing values with np.NaN, but needs
    help identifying other flags used by the USGS to indicate no data is 
    availabiel.  Function returns the completed DataFrame, and a dictionary 
    designed to contain all missing value counts that is initialized with
    days missing between the first and last date of the file."""
    
    # define column names
    colNames = ['agency_cd', 'site_no', 'Date', 'Discharge', 'Quality']

    # open and read the file
    DataDF = pd.read_csv(fileName, header=1, names=colNames,  
                         delimiter=r"\s+",parse_dates=[2], comment='#',
                         na_values=['Eqp'])
    DataDF = DataDF.set_index('Date')
    
    # quantify the number of missing values
    MissingValues = DataDF["Discharge"].isna().sum()
    
    return( DataDF, MissingValues )

def ClipData( DataDF, startDate, endDate ):
    """This function clips the given time series dataframe to a given range 
    of dates. Function returns the clipped dataframe and and the number of 
    missing values."""
    #For cliping data
    DataDF=DataDF[startDate:endDate]
    
    #Counting nodata values
    MissingValues = DataDF["Discharge"].isna().sum()
    
    return( DataDF, MissingValues )

def CalcTqmean(Qvalues):
    """This function computes the Tqmean of a series of data, typically
       a 1 year time series of streamflow, after filtering out NoData
       values.  Tqmean is the fraction of time that daily streamflow
       exceeds mean streamflow for each year. Tqmean is based on the
       duration rather than the volume of streamflow. The routine returns
       the Tqmean value for the given data array."""
    #Removing Nas, no data  values
    Qvalues=Qvalues.dropna()
    
    #Calculating mean of Qvalues
    meanQ=Qvalues.mean()
    
    #Calculating the fraction of time when Qvalues exceeds mean value
    Tqmean=(((Qvalues > meanQ).sum())/len(Qvalues))
    return ( Tqmean )

def CalcRBindex(Qvalues):
    """This function computes the Richards-Baker Flashiness Index
       (R-B Index) of an array of values, typically a 1 year time
       series of streamflow, after filtering out the NoData values.
       The index is calculated by dividing the sum of the absolute
       values of day-to-day changes in daily discharge volumes
       (pathlength) by total discharge volumes for each year. The
       routine returns the RBindex value for the given data array."""
    #Removing Nas,no data values
    Qvalues=Qvalues.dropna()
    
    #Changes inflow
    ChangQ= Qvalues.diff()
    
    #Removing the change in flow values with no differences
    ChangQ=ChangQ.dropna()
    
    #Calculating the absolute values of change in flow and it's sum
    abCQ=abs(ChangQ)
    abCQT=abCQ.sum()
    
    #Total discharge
    TQvalues=Qvalues.sum()
    
    #Calculating the ratio as RBindex
    RBindex=abCQT/TQvalues
    
    return ( RBindex )

def Calc7Q(Qvalues):
    """This function computes the seven day low flow of an array of 
       values, typically a 1 year time series of streamflow, after 
       filtering out the NoData values. The index is calculated by 
       computing a 7-day moving average for the annual dataset, and 
       picking the lowest average flow in any 7-day period during
       that year.  The routine returns the 7Q (7-day low flow) value
       for the given data array."""
    Qvalues=Qvalues.dropna()   #Removing na
    #Calculating rolling mean and selecting the minimum value
    val7Q=Qvalues.rolling(window=7).mean().min()
    
    return ( val7Q )

def CalcExceed3TimesMedian(Qvalues):
    """This function computes the number of days with flows greater 
       than 3 times the annual median flow. The index is calculated by 
       computing the median flow from the given dataset (or using the value
       provided) and then counting the number of days with flow greater than 
       3 times that value.   The routine returns the count of events greater 
       than 3 times the median annual flow value for the given data array."""
    #Removing Nans
    Qvalues=Qvalues.dropna()
    
    #Creating threshold
    Threshold=3*Qvalues.median()
    
    #Counts the discharge which are greater than the threshold and it's sum
    median3x=(Qvalues>Threshold).sum()
    return ( median3x )

def GetAnnualStatistics(DataDF):
    """This function calculates annual descriptive statistcs and metrics for 
    the given streamflow time series.  Values are retuned as a dataframe of
    annual values for each water year.  Water year, as defined by the USGS,
    starts on October 1."""
    # define column names for a annual dataframe,WYDataDF
    colNamesA = ['site_no', 'Mean Flow', 'Peak Flow', 'Median',
                 'Coeff Var','Skew','TQmean','R-B Index','7Q','3xMedian']
    
    #annual data resampling, as water year starts from sept to oct
    annualdata=DataDF.resample('AS-OCT').mean()
    
    #Creating a empty dataframe with columnnames and index
    WYDataDF=pd.DataFrame(0,index=annualdata.index, columns=colNamesA)
    
    #Selecting variables for water year
    WY=DataDF.resample('AS-OCT')
    
    #Creating the data for each columns
    WYDataDF['site_no']=WY['site_no'].mean()
    WYDataDF['Mean Flow']=WY['Discharge'].mean()
    WYDataDF['Peak Flow']=WY['Discharge'].max()
    WYDataDF['Median']=WY['Discharge'].median()
    WYDataDF['Coeff Var']=(WY['Discharge'].std()/WY['Discharge'].mean())*100
    WYDataDF['Skew']=WY.apply({'Discharge': lambda x: stats.skew(x,nan_policy='omit',bias=False)},raw=True)
    WYDataDF['TQmean']=WY.apply({'Discharge': lambda x: CalcTqmean(x)})
    WYDataDF['R-B Index']=WY.apply({'Discharge': lambda x: CalcRBindex(x)})
    WYDataDF['7Q']=WY.apply({'Discharge': lambda x: Calc7Q(x)})
    WYDataDF['3xMedian']=WY.apply({'Discharge': lambda x: CalcExceed3TimesMedian(x)})
    
    
    return ( WYDataDF )

def GetMonthlyStatistics(DataDF):
    """This function calculates monthly descriptive statistics and metrics 
    for the given streamflow time series.  Values are returned as a dataframe
    of monthly values for each year."""
    # define column names for a monthly dataframe,WYDataDF
    colNamesB = ['site_no', 'Mean Flow','Coeff Var','TQmean','R-B Index']
    
    #monthly data resampling,
    monthlydata=DataDF.resample('MS').mean()
    
    #Creating a empty dataframe with columnnames and index
    MoDataDF=pd.DataFrame(0,index=monthlydata.index, columns=colNamesB)
    
    #Selecting variables for monthly data set
    MD=DataDF.resample('MS')
    
    #Creating the data for each columns
    MoDataDF['site_no']=MD['site_no'].mean()
    MoDataDF['Mean Flow']=MD['Discharge'].mean()
    MoDataDF['Coeff Var']=(MD['Discharge'].std()/MD['Discharge'].mean())*100
    MoDataDF['TQmean']=MD.apply({'Discharge': lambda x: CalcTqmean(x)})
    MoDataDF['R-B Index']=MD.apply({'Discharge': lambda x: CalcRBindex(x)})
   
    return ( MoDataDF )

def GetAnnualAverages(WYDataDF):
    """This function calculates annual average values for all statistics and
    metrics.  The routine returns an array of mean values for each metric
    in the original dataframe."""
    #Calculating mean of each column
    AnnualAverages=WYDataDF.mean(axis=0)
    
    return( AnnualAverages )

def GetMonthlyAverages(MoDataDF):
    """This function calculates annual average monthly values for all 
    statistics and metrics.  The routine returns an array of mean values 
    for each metric in the original dataframe."""
    #Create an empty dataframe
    cols=['site_no','Mean Flow','Coeff Var','TQmean','R-B Index']
    MonthlyAverages= pd.DataFrame(0,index=range(1,13),columns=cols)
    #Monthly Average sites
    for n in range(0,12):
       MonthlyAverages.iloc[n,0]= MoDataDF['site_no'][::12].mean()
    
    #Defining months
    index=[(0,3),(1,4),(2,5),(3,6),(4,7),(5,8),(6,9),(7,10),(8,11),(9,0),(10,1),(11,2)]
    
    
    #For other variables
    for (n,m) in index:
        MonthlyAverages.iloc[n,1]=MoDataDF['Mean Flow'][m::12].mean()#For monthly mean flow average 
    for (n,m) in index:  
        MonthlyAverages.iloc[n,2]=MoDataDF['Coeff Var'][m::12].mean()  #For monthly Coeff average
    for (n,m) in index:
        MonthlyAverages.iloc[n,3]=MoDataDF['TQmean'][m::12].mean()     #For monthly TQ mean average
    for (n,m) in index:
        MonthlyAverages.iloc[n,4]=MoDataDF['R-B Index'][m::12].mean()  #For month R-B index average
        
    return( MonthlyAverages )

# the following condition checks whether we are running as a script, in which 
# case run the test code, otherwise functions are being imported so do not.
# put the main routines from your code after this conditional check.

if __name__ == '__main__':

    # define filenames as a dictionary
    # NOTE - you could include more than jsut the filename in a dictionary, 
    #  such as full name of the river or gaging site, units, etc. that would
    #  be used later in the program, like when plotting the data.
    fileName = { "Wildcat": "WildcatCreek_Discharge_03335000_19540601-20200315.txt",
                 "Tippe": "TippecanoeRiver_Discharge_03331500_19431001-20200315.txt" }
    
    # define blank dictionaries (these will use the same keys as fileName)
    DataDF = {}
    MissingValues = {}
    WYDataDF = {}
    MoDataDF = {}
    AnnualAverages = {}
    MonthlyAverages = {}
    
    # process input datasets
    for file in fileName.keys():
        
        print( "\n", "="*50, "\n  Working on {} \n".format(file), "="*50, "\n" )
        
        DataDF[file], MissingValues[file] = ReadData(fileName[file])
        print( "-"*50, "\n\nRaw data for {}...\n\n".format(file), DataDF[file].describe(), "\n\nMissing values: {}\n\n".format(MissingValues[file]))
        
        # clip to consistent period
        DataDF[file], MissingValues[file] = ClipData( DataDF[file], '1969-10-01', '2019-09-30' )
        print( "-"*50, "\n\nSelected period data for {}...\n\n".format(file), DataDF[file].describe(), "\n\nMissing values: {}\n\n".format(MissingValues[file]))
        
        # calculate descriptive statistics for each water year
        WYDataDF[file] = GetAnnualStatistics(DataDF[file])
        
        # calcualte the annual average for each stistic or metric
        AnnualAverages[file] = GetAnnualAverages(WYDataDF[file])
        
        print("-"*50, "\n\nSummary of water year metrics...\n\n", WYDataDF[file].describe(), "\n\nAnnual water year averages...\n\n", AnnualAverages[file])

        # calculate descriptive statistics for each month
        MoDataDF[file] = GetMonthlyStatistics(DataDF[file])

        # calculate the annual averages for each statistics on a monthly basis
        MonthlyAverages[file] = GetMonthlyAverages(MoDataDF[file])
        
        print("-"*50, "\n\nSummary of monthly metrics...\n\n", MoDataDF[file].describe(), "\n\nAnnual Monthly Averages...\n\n", MonthlyAverages[file])
        
    #Output Files
    #ANNUAL METRICES, from water years
    WY_wild=WYDataDF['Wildcat']
    WY_wild['Station']='Wildcat'
    WY_tippe=WYDataDF['Tippe']
    WY_tippe['Station']='Tippe'
    WY_wild=WY_wild.append(WY_tippe)  #Combining two datasets
    WY_wild.to_csv('Annual_Metrics.csv',sep=',',index=True) #Writing to csv files
    
    #Monthly metrics
    Mo_wild=MoDataDF['Wildcat']
    Mo_wild['Station']='Wildcat'
    Mo_tippe=MoDataDF['Tippe']
    Mo_tippe['Station']='Tippe'
    Mo_wild=Mo_wild.append(Mo_tippe)  #Combining two datasets
    Mo_wild.to_csv('Monthly_Metrics.csv',sep=',',index=True)   #Writing to csv file
    
    #Annual average metrics(txt file)
    AA_wild=AnnualAverages['Wildcat']
    AA_wild['Station']='Wildcat'
    AA_tippe=AnnualAverages['Tippe']
    AA_tippe['Station']='Tippe'
    AA_wild=AA_wild.append(AA_tippe)  #Combining two datasets
    AA_wild.to_csv('Average_Annual_Metrics.txt',sep='\t',index=True)
    
    #Monthly average metrics(txt file)
    MA_wild=MonthlyAverages['Wildcat']
    MA_wild['Station']='Wildcat'
    MA_tippe=MonthlyAverages['Tippe']
    MA_tippe['Station']='Tippe'
    MA_wild=MA_wild.append(MA_tippe)  #Combining two datasets
    MA_wild.to_csv('Average_Monthly_Metrics.txt',sep='\t',index=True)