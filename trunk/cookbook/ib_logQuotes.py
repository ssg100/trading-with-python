'''
Created on May 5, 2013
Copyright: Jev Kuznetsov
License: BSD

Program to log tick events to a file

example usage:
    > python ib_logQuotes.py SPY,VXX,XLE     
    
    start with -v option to show all incoming events


'''

import argparse # command line argument parser
import datetime as dt # date and time functions
import time # time module for timestamping
import os # used to create directories
import sys # used to print a dot to a terminal without new line

#--------ibpy imports ----------------------
from ib.ext.Contract import Contract
from ib.opt import ibConnection, message


# tick type definitions, see IB api manual
priceTicks = {1:'bid',2:'ask',4:'last',6:'high',7:'low',9:'close', 14:'open'}
sizeTicks = {0:'bid',3:'ask',5:'last',8:'volume'}

class TickLogger(object):
    ''' class for handling incoming ticks and saving them to file 
        will create a subdirectory 'tickLogs' if needed and start logging
        to a file with current timestamp in its name.
        All timestamps in the file are in seconds relative to start of logging
    
    '''
    def __init__(self,tws, subscriptions):
        ''' init class, register handlers '''
      
        tws.register(self._priceHandler,message.TickPrice)
        tws.register(self._sizeHandler,message.TickSize)
        
        self.subscriptions = subscriptions        
        
        # save starting time of logging. All times will be in seconds relative
        # to this moment
        self._startTime = time.time() 
        
        # create data directory if it does not exist
        if not os.path.exists('tickLogs'): os.mkdir('tickLogs')     
        
        # open data file for writing
        fileName = 'tickLogs\\tickLog_%s.csv' % dt.datetime.now().strftime('%H_%M_%S')
        print 'Logging ticks to ' , fileName
        self.dataFile = open(fileName,'w')        
    
 
    def _priceHandler(self,msg):
        ''' price tick handler '''
        data = [self.subscriptions[msg.tickerId].m_symbol,'price',priceTicks[msg.field],msg.price] # data, second field is price tick type
        self._writeData(data)
        
    def _sizeHandler(self,msg):   
        ''' size tick handler '''
        data = [self.subscriptions[msg.tickerId].m_symbol,'size',sizeTicks[msg.field],msg.size]
        self._writeData(data)
    
    def _writeData(self,data):
        ''' write data to log file while adding a timestamp '''
        timestamp = '%.3f' % (time.time()-self._startTime) # 1 ms resolution
        dataLine = ','.join(str(bit) for bit in [timestamp]+data) + '\n'
        self.dataFile.write(dataLine)
   
    def flush(self):
        ''' commits data to file'''
        self.dataFile.flush()
     
    def close(self):
        '''close file in a neat manner '''
        print 'Closing data file'
        self.dataFile.close()


def printMessage(msg):
    ''' function to print all incoming messages from TWS '''
    print '[msg]:', msg


def createContract(symbol):
    ''' create contract object '''
    c = Contract()
    c.m_symbol = symbol
    c.m_secType= "STK"
    c.m_exchange = "SMART"
    c.m_currency = "USD"
    
    return c

#--------------main script------------------

if __name__ == '__main__':
    
    #-----------parse command line arguments    
    parser = argparse.ArgumentParser(description='Log ticks for a set of stocks')
    
    
    parser.add_argument("symbols",help = 'symbols separated by coma: SPY,VXX')
    parser.add_argument("-v", "--verbose", help="show all incoming messages",
                    action="store_true")    
    
    args = parser.parse_args()

    symbols = args.symbols.strip().split(',')
    print 'Logging ticks for:',symbols
    
    
    #---create subscriptions  dictionary. Keys are subscription ids   
    subscriptions = {}
    for idx, symbol in enumerate(symbols):
        subscriptions[idx+1] = createContract(symbol)
    
    tws = ibConnection()
    logger = TickLogger(tws,subscriptions)
    
    # print all messages to the screen if verbose option is chosen
    if args.verbose:
        print 'Starting in verbose mode'
        tws.registerAll(printMessage)
    
    
    tws.connect()

    #-------subscribe to data
    for subId, c in subscriptions.iteritems():
        tws.reqMktData(subId,c,"",False)

    #------start a loop that must be interrupted with Ctrl-C
    print 'Press Ctr-C to stop loop'

    try:
        while True:
            time.sleep(2) # wait a little
            logger.flush() # commit data to file
            sys.stdout.write('.') # print a dot to the screen
                
                
    except KeyboardInterrupt:
        print 'Interrupted with Ctrl-c'    
    
    logger.close()             
    tws.disconnect()
    print 'All done'
    