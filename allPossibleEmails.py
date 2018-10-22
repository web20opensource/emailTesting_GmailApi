#title           :allPossibleEmails.py
#description     :This py file is a dict for all the possible emails we can send actually in Marketing Cloud Salesforce.
#dependencies     :GMAIL API, python 3.6
#author             :Mario Ruiz <web2.0opensource@gmail.com>
#date            :09/18/2017
#version         :1    
#usage             :it is included in getReceivedEmails.py
#notes           :
#bash_version    :4.4.12(1)-release
#==============================================================================

countryDictionary = {
  'USA':{
    'MGO':{
        'emailsFound':0
    } , 
    'WAP':{
    'emailsFound':0}
  }
}

allPossibleEmails = {
  'USA-EN':[
    'MGO-USA-EN-Account_Locked',
    'MGO-USA-EN-Welcome_MGO'
    ],
  'USA-ES':[
    'MGO-USA-ES-Account_Locked',
    'MGO-USA-ES-Welcome_MGO'
    ],
  'WAP-EN':[
    'WAP-USA-EN-Account_Locked',
    'WAP-USA-EN-Welcome_MGO'
    ],
  'WAP-ES':[
    'WAP-USA-ES-Account_Locked',
    'WAP-USA-ES-Welcome_MGO'
    ]
}
