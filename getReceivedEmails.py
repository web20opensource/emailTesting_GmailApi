#title           :getReceivedEmails.py
#description     :This script will get a summary of the emails delivered after triggered/delivered by Email Service
#dependencies     :GMAIL API, python 3.6, messages.py, allPossibleEmails.py , testLinks.py, messages.py
#author             :Mario Ruiz <web2.0opensource@gmail.com>
#date            :09/18/2017
#version         :1    
#usage             :python getReceivedEmails.py
#notes           :
#bash_version    :4.4.12(1)-release
#==============================================================================

from __future__ import print_function

import httplib2
import os
import base64
import email
import re
import importlib
import sys
import json


from apiclient import errors
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from datetime import date, timedelta


#import data dicts
from messages import *
from allPossibleEmails import *
from testLinks import *

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API test'


#following from Python cookbook, #475186
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
def has_colours(stream):
    if not hasattr(stream, "isatty"):
        return False
    if not stream.isatty():
        return False # auto color only on TTYs
    try:
        import curses
        curses.setupterm()
        return curses.tigetnum("colors") > 2
    except:
        # guess false in case of error
        return False
has_colours = has_colours(sys.stdout)


def findField(headers=[], lookFor=""):
    for  header in headers:
        #print (header)
        #print ()
        if header['name'] == lookFor :
            return header['value'].encode('utf-8')
            break


def GetMimeMessage(service, user_id, msg_id):
    """Get a Message and use it to create a MIME Message.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

    Returns:
    A MIME Message, consisting of data from Message.
    """
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        if ('data' in message['payload']['body']):
            msg_str = base64.urlsafe_b64decode( message['payload']['body']['data'] );
        else:
            msg_str = base64.urlsafe_b64decode(
                    message['payload']['parts'][0]['body']['data']
                    + message['payload']['parts'][1]['body']['data']
                  );

        subject = findField( message['payload']['headers'] , "Subject" )

        #print (message['payload']['parts'][1]['body']['data']);
        #print (user_id)
        #print (msg_id)
        #exit()
        msg_str = msg_str.decode('utf-8').strip().replace('\u200b',"")

    #mime_msg = email.message_from_string(msg_str)

        return (subject, msg_str)
    except errors.HttpError:
        print ('An error occurred  reading the message' )

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def ListMessagesMatchingQuery(service, user_id='me', query=''):
      """List all Messages of the user's mailbox matching the query.
      Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      query: String used to filter messages returned.
      Eg.- 'from:user@some_domain.com' for Messages from a particular sender.
      Returns:
      List of Messages that match the criteria of the query. Note that the
      returned list contains Message IDs, you must use get with the
      appropriate ID to get the details of a Message.
      """
      try:
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])
        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
            if (response['resultSizeEstimate'] > 0):
                messages.extend(response['messages'])
        return messages
      except errors.HttpError as error:
        print ('An error occurred: %s' % error)


def getEmailId(mailBody):
    emailId = ""
    #EV-POSTCAN-CAN-EN-Welcome_MGO
    idsRegExPostCan = re.compile(r'[A-Z]{2}-[A-Z][A-Z]{6}-[A-Z]{3}-[A-Z]{2}-[A-Za-z_]+')
    idsRegExMgo = re.compile(r'[A-Z]{2}-[A-Z]{3}-[A-Z]{3}-[A-Z]{2}-[A-Za-z_]+')

    if (len(idsRegExPostCan.findall(mailBody)) > 0):
        return idsRegExPostCan.findall(mailBody)[0]
    
    if (len(idsRegExMgo.findall(mailBody)) > 0):
          return idsRegExMgo.findall(mailBody)[0]

    print(mailBody)
    print("it sucks! :( ")
    return "NOTFOUND-EMAIL-NOT-MATCHING-ANY-REGEXP"

def testEmailExists(allEmailsFound, emailsExpected, emailsNotFound):
    for emailId in emailsExpected:
        if ( emailId in allEmailsFound):
            print ("[ok] " + emailId + " found.")
        else:
            print ("[*******error*******] "+ "not found:" + emailId)
            emailsNotFound.append(emailId)
    return emailsNotFound

def main():
    """
    Creates a Gmail API service object and outputs the message count of a specified sender
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    sumAll = 0

    #emails got from the query used below
    messages = {}

    #links used in the emails
    emailLinks = {};
    yesterday = date.today() - timedelta(1)

    for sender in senders:
        messages.update ( {
            sender : ListMessagesMatchingQuery(
                    service,
                    user_id='me',
                    query='from:' + sender.lower() + '@moneygram.com' + ' after:2018/9/11' #+ yesterday.strftime('%y/%m/%d')
            )
        })
    #labels = results.get('labels', [])

    if not messages:
        print('No messages found.')
    else:
        #DEV-MGO-AUS-EN-Account_Locked
        #should use a different technic as QA is only 0:2 and PROD is 0:4
        #might be get indexOf dash (-) and from there keep going...
        #QA-MGO-AUS-EN-Account_Locked
        #QA-POSTCAN-AUS-EN-Account_Locked
        emailIds = []
        subjects = {}
        for message in messages:
            mailObj = messages.get(message)
            if len( mailObj ) :
                for idObj in mailObj:
                    (subject , mailBody) = GetMimeMessage(service, 'me', idObj['id'])
                    try:
                        idEmail = getEmailId(mailBody)
                        #MGO-ITA-IT-Receiver_
                        if (idEmail[13:23] == '-Receiver_' or idEmail[17:27] == '-Receiver_'):
                            print("skipped: %s" , idEmail)
                            continue
                    except Exception as e:
                        #print (mailBody)
                        print (mailBody)
                        print ("there was an exception when trying to find the email id.... there's no such id or the regexp is not matching it. ")
                        print(idEmail)
                        print(e);
                        print (subject)
                        exit()
                    # EV, QA, XT, OD
                    try:
                        (environment , partner , country , language , event) = re.split("-", idEmail)
                    except Exception as e:
                        print(idEmail)
                        print (subject)
                        exit()
                    #if (environment != "EV"):
                    #    continue;
                    # environment = idEmail[0:2]

                    if (environment == "NOTFOUND"):
                      print(mailBody)
                      print("NOTFOUND-EMAIL-NOT-MATCHING-ANY-REGEXP")
                      exit()

                    if (environment != "OD"):
                      print(idEmail + " skipped")
                      continue

                    #if ( partner != "POSTCAN"):
                    #  print(idEmail + " skipped")
                    #  continue
                    """                        
                    if ( country != "CAN"):
                        print ("skipped " +  idEmail)
                        continue;

                    if ( event != "Cancel_Confirmation"):
                        print ("skipped " +  idEmail)
                        continue;

                    if ( language != "FR" ):
                        print ("skipped" + idEmail)
                        continue;

                    if ( partner != "POSTCAN" ):
                        print ("skipped %s", idEmail)
                        continue;
                    """

                    """print(environment)
                    partner = idEmail[3:6]
                    print(partner)
                    country = idEmail[7:10]
                    print(country)
                    language = idEmail[11:13]
                    print(language)
                    event= idEmail[14:]
                    print(event)
                    """

                    print(partner)
                    print(country)
                    print(language)
                    print(event)
                    print ("got email: " + idEmail)
                    subjects[idEmail[3:]] = subject
                    dictSubjMessage = my_dict_get(event, country.upper() +  '-' + language.upper(), partner)
                    try:
                        print (dictSubjMessage.encode('utf-8'))
                    except Exception as e:
                        print(e);
                        print (dictSubjMessage)
                    print (subject)
                    #test if subject is different from the one expected
                    if (dictSubjMessage.encode('utf-8') != subject):
                        print ("different Subject found ", event , language, country, subject, environment)
                        exit()
                    #test if any link is getting 404 reponse
                    emailLinks.update(testLinks(mailBody));
                    #if (testLinks(mailBody) == False):
                    #    print ("broken link found", event , language, country, subject, environment)
                    #    exit()
                    if (idEmail[3:] not in emailIds):
                        emailIds.append(idEmail[3:])
                        if (country in ("USA","CAN") ):
                            countryDictionary[country][partner]['emailsFound'] += 1
                        else:
                            countryDictionary[country]['emailsFound'] += 1
                        sumAll += 1
                    
                    if (partner != "MGO"):
                        fileName = language+'-'+country+'/'+partner+'/'+message+".html"
                    else:
                        fileName = language+'-'+country+'/'+message+".html"
                    
                    os.makedirs(os.path.dirname(fileName.lower()), exist_ok=True)
                    with open(fileName.lower(), "w+") as text_file:
                        #print(mailBody)
                        print(f"{mailBody}", file=text_file)
            else:
                print(message+"\n")
        print(len(emailIds))
        print (countryDictionary)
        print ("total found were: ", sumAll)

        #print a summary of emails matched and expected!
        print (emailIds)
        print (subjects)

        """for (emailId in emailIds):
            #USA
            for groupEmail in countryDictionary['USA']['emailsAvailable']:
                #foreach group
        """
        emailsNotFound = []

        # run usa-en tests
        testEmailExists (emailIds,allPossibleEmails['USA-EN'],emailsNotFound)
        # run usa-es tests
        testEmailExists (emailIds,allPossibleEmails['USA-ES'],emailsNotFound)
        # run wap-en tests
        testEmailExists (emailIds,allPossibleEmails['WAP-EN'],emailsNotFound) 
        # run wap-es tests
        testEmailExists (emailIds,allPossibleEmails['WAP-ES'],emailsNotFound)
        # run aus-en tests
        testEmailExists (emailIds,allPossibleEmails['AUS-EN'],emailsNotFound) 

        #CAN-13
        # run can-en tests
        testEmailExists (emailIds,allPossibleEmails['CAN-EN'],emailsNotFound) 
        # run can-fr tests
        testEmailExists (emailIds,allPossibleEmails['CAN-FR'],emailsNotFound) 

        #CP-93
        # run postcan-en tests
        testEmailExists (emailIds,allPossibleEmails['POSTCAN-EN'],emailsNotFound) 
        # run postcan-fr tests
        testEmailExists (emailIds,allPossibleEmails['POSTCAN-FR'],emailsNotFound) 

        # run bhs-en tests
        #testEmailExists (emailIds,allPossibleEmails['BHS-EN'],emailsNotFound) 
        # run deu-en tests
        testEmailExists (emailIds,allPossibleEmails['DEU-EN'],emailsNotFound) 
        # run deu-de tests
        testEmailExists (emailIds,allPossibleEmails['DEU-DE'],emailsNotFound) 
        # run esp-en tests
        testEmailExists (emailIds,allPossibleEmails['ESP-EN'],emailsNotFound) 
        # run esp-es tests
        testEmailExists (emailIds,allPossibleEmails['ESP-ES'],emailsNotFound) 
        # run fra-en tests
        testEmailExists (emailIds,allPossibleEmails['FRA-EN'],emailsNotFound) 
        # run fra-fr tests
        testEmailExists (emailIds,allPossibleEmails['FRA-FR'],emailsNotFound) 
        # run gbr-en tests
        testEmailExists (emailIds,allPossibleEmails['GBR-EN'],emailsNotFound) 
        # run jpn-en tests
        #testEmailExists (emailIds,allPossibleEmails['JPN-EN'],emailsNotFound) 
        
        #CCPS        
        #CPP-25
        # run mex-en tests
        testEmailExists (emailIds,allPossibleEmails['MEX-EN'],emailsNotFound) 
        # run bra-en tests
        testEmailExists (emailIds,allPossibleEmails['BRA-EN'],emailsNotFound) 


        # BUCKET SITES - PHASE 1&2
        # MCT-1900, MCT-1950, MCT-1995, BUCKET-42
        # run nld-en tests
        testEmailExists (emailIds,allPossibleEmails['NLD-EN'],emailsNotFound) 
        # run nor-en tests
        testEmailExists (emailIds,allPossibleEmails['NOR-EN'],emailsNotFound)         
        # run pol-en tests
        testEmailExists (emailIds,allPossibleEmails['POL-EN'],emailsNotFound)         
        # run prt-en tests
        testEmailExists (emailIds,allPossibleEmails['PRT-EN'],emailsNotFound)         
        # run prt-en tests
        testEmailExists (emailIds,allPossibleEmails['SWE-EN'],emailsNotFound) 
        # run irl-en tests
        testEmailExists (emailIds,allPossibleEmails['IRL-EN'],emailsNotFound) 
        # run dnk-en tests
        testEmailExists (emailIds,allPossibleEmails['DNK-EN'],emailsNotFound)
        # run aut-en tests
        testEmailExists (emailIds,allPossibleEmails['AUT-EN'],emailsNotFound) 
        # run bel-en tests
        testEmailExists (emailIds,allPossibleEmails['BEL-EN'],emailsNotFound) 
        # run grc-en tests
        testEmailExists (emailIds,allPossibleEmails['GRC-EN'],emailsNotFound) 

        # BUCKET SITES - PHASE 3
        # run ita-en tests
        testEmailExists (emailIds,allPossibleEmails['ITA-EN'],emailsNotFound) 
        # run ita-it tests
        testEmailExists (emailIds,allPossibleEmails['ITA-IT'],emailsNotFound) 
        # run bgr-en tests
        testEmailExists (emailIds,allPossibleEmails['BGR-EN'],emailsNotFound) 
        # run hrv-en tests
        testEmailExists (emailIds,allPossibleEmails['HRV-EN'],emailsNotFound) 
        # run cze-en tests
        testEmailExists (emailIds,allPossibleEmails['CZE-EN'],emailsNotFound) 
        # run est-en tests
        testEmailExists (emailIds,allPossibleEmails['EST-EN'],emailsNotFound) 
        # run fin-en tests
        testEmailExists (emailIds,allPossibleEmails['FIN-EN'],emailsNotFound) 
        # run hun-en tests
        testEmailExists (emailIds,allPossibleEmails['HUN-EN'],emailsNotFound) 
        # run isl-en tests
        testEmailExists (emailIds,allPossibleEmails['ISL-EN'],emailsNotFound) 
        # run lva-en tests
        testEmailExists (emailIds,allPossibleEmails['LVA-EN'],emailsNotFound) 
        # run ltu-en tests
        testEmailExists (emailIds,allPossibleEmails['LTU-EN'],emailsNotFound) 
        # run lux-en tests
        testEmailExists (emailIds,allPossibleEmails['LUX-EN'],emailsNotFound) 
        # run mlt-en tests
        testEmailExists (emailIds,allPossibleEmails['MLT-EN'],emailsNotFound) 
        # run rou-en tests
        testEmailExists (emailIds,allPossibleEmails['ROU-EN'],emailsNotFound) 
        # run svk-en tests
        testEmailExists (emailIds,allPossibleEmails['SVK-EN'],emailsNotFound) 
        # run svn-en tests
        testEmailExists (emailIds,allPossibleEmails['SVN-EN'],emailsNotFound) 
        # run che-en tests
        testEmailExists (emailIds,allPossibleEmails['CHE-EN'],emailsNotFound) 

        if ( len(emailsNotFound) > 0 ):
            print ("emails not found:")
            print (emailsNotFound)
        else:
            print ("all emails were found.")

        print("found links available in emails at the file emailLinks")
        with open("emailLinks.json".lower(), "w+") as text_file:
            #print(mailBody)
            print(f"{json.dumps(emailLinks)}", file=text_file)
        """
        for emailId in allPossibleEmails['USA-EN']:
            if ( emailId in emailIds):
                print (emailId + " found.")
            else:
                print ("------------------------------ not found: " + emailId)
                emailsNotFound.append(emailId)
        """
        #print (senders)


if __name__ == '__main__':
    main()
