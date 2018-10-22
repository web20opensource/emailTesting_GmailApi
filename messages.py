#title           :messages.py
#description     :This py file stores the different Subjetcs used in all emails / all countries.
#dependencies	 :GMAIL API, python 3.6
#author			 :Mario Ruiz <web2.0opensource@moneygram.com>
#date            :09/18/2017
#version         :1    
#usage			 :python getReceivedEmails.py
#notes           :
#bash_version    :4.4.12(1)-release
#==============================================================================

senders = {
        'Account_Locked':{'extK':'35'},
        'Welcome_MGO': {'extK':'85'}
        }

senders['Welcome_MGO']['USA-EN'] = {}
senders['Welcome_MGO']['USA-ES'] = {}

#USA-EN language Subjects
senders['Account_Locked']['USA-EN'] = "Account Locked"

#Walmart 
senders['Welcome_MGO']['USA-ES']['WAP'] = "Bienvenido al servicio de transferencia de dinero de Walmart"
senders['Welcome_MGO']['USA-EN']['WAP'] = "Welcome to Walmart Money Transfers Online"

#USA-ES language Subjects
senders['Account_Locked']['USA-ES'] = "Cuenta bloqueada"


def my_dict_get(eventKey, countryLang, partner):
    try:
        event = senders[eventKey]
    except Exception as e:
        print(e)
        print ("Event has not been added yet, please add it to the dict")
        print ("output form line 156 - messages.py file")
        exit()
    try:
        if (countryLang[0:3] == "USA" and eventKey == "Welcome_MGO"):
            return senders[eventKey][countryLang][partner];
        else:
            return senders[eventKey][countryLang];
    except KeyError:
        lang = getBaseTrans(countryLang[4:6])
        print ("language will be based in the ", lang)
        return my_dict_get(eventKey,lang,partner)


#mainly purpose is all new EU sites - Bucket sites phase 1 - new 10 countries
def getBaseTrans(x):
    return {
            'EN': 'USA-EN',
            'ES': 'USA-ES',
            'FR': 'FRA-FR',
            'DE': 'DEU-DE'
            }[x]

#print (getBaseTrans("FR"))
#print ("CAN-FR"[4:6])
#print  (my_dict_get("Account_Locked","CAN-FR" ))


print ("successfully imported!")
